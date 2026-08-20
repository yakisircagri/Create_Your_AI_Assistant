import json
import os
from dotenv import load_dotenv

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.models.agent import Agent
from app.models.agent_tool import AgentTool
from app.models.conversation import Conversation
from app.models.conversation_message import ConversationMessage
from app.models.mcp_server import MCPServer
from app.models.mcp_tools import MCPTool
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
)
from app.services.llm_services import LLMService
from app.services.mcp.client import MCPClient

load_dotenv()

router = APIRouter(
    prefix="/api/conversations",
    tags=["conversations"],
)



@router.post("", response_model=ConversationResponse)
async def create_conversation(
        data: ConversationCreate,
        db: AsyncSession = Depends(get_db),
):
    agent = await db.get(Agent,data.agent_id )

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    conversation = Conversation(
        agent_id = data.agent_id,
        title = data.title,
    )

    db.add(conversation)

    await db.commit()
    await db.refresh(conversation)

    return conversation



@router.get("", response_model=list[ConversationResponse])
async def get_conversations(
        agent_id: int | None = None,
        db: AsyncSession = Depends(get_db),
):
    query = select(Conversation).order_by(Conversation.id.desc())

    if agent_id is not None:
        query = query.where(Conversation.agent_id == agent_id)

    result = await db.scalars(query)

    return result.all()



@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
        conversation_id: int,
        db: AsyncSession = Depends(get_db),
):
    conversation = await db.get(Conversation, conversation_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation



@router.delete("/{conversation_id}")
async def delete_conversation(
        conversation_id: int,
        db: AsyncSession = Depends(get_db),
):
    conversation = await db.get(Conversation, conversation_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.delete(conversation)
    await db.commit()

    return {
        "message": "Conversation deleted successfully",
    }



@router.post("/{conversation_id}/messages")
async def create_message(
        conversation_id: int,
        data: MessageCreate,
        x_mcp_token: str | None = Header(
            default=None,
            alias="X-MCP-Token",
        ),
        db: AsyncSession = Depends(get_db),
):
    conversation = await db.get(Conversation, conversation_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    agent = await db.get(Agent, conversation.agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    result = await db.execute(
        select(MCPTool)
        .join(
            AgentTool,
            AgentTool.mcp_tool_id == MCPTool.id
        )
        .where(
            AgentTool.agent_id == agent.id
        )
    )

    selected_tools = result.scalars().all()

    llm = LLMService()

    openai_tools = llm.mcp_tools_to_openai_tools(selected_tools)

    result = await db.scalars(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation.id)
        .order_by(ConversationMessage.id.asc())
    )

    previous_messages = result.all()

    messages = [
        {
            "role" : "system",
            "content" : agent.system_prompt or ""
        }
    ]

    for previous_message in previous_messages:

        if previous_message.role == "user":
            messages.append({
                "role": "user",
                "content": previous_message.content or "",
            })

        elif previous_message.role == "assistant":
            assistant_message = {
                "role": "assistant",
                "content": previous_message.content,
            }

            if previous_message.tool_calls:

                tool_calls = json.loads(
                    previous_message.tool_calls
                )
                assistant_message["tool_calls"] = tool_calls
            messages.append(assistant_message)

        elif previous_message.role == "tool":
            messages.append({
                "role": "tool",
                "tool_call_id": previous_message.tool_call_id,
                "content": previous_message.content or "",
            })

    user_message = ConversationMessage(
        conversation_id = conversation_id,
        role = "user",
        content = data.content,
    )

    db.add(user_message)

    await db.commit()
    await db.refresh(user_message)

    messages.append({
        "role" : "user",
        "content" : data.content or "",
    })

    max_iterations = 5

    for _ in range(max_iterations):

        print("======== FINAL MESSAGES TO OPENAI ========")
        for i, msg in enumerate(messages):
            print(f"[{i}] {msg}")
        print("==========================================")

        response = await llm.client.chat.completions.create(
            model=agent.model,
            messages=messages,
            tools=openai_tools or [],
        )

        message = response.choices[0].message

        print("======== LLM RESPONSE ========")
        print("CONTENT:", message.content)
        print("TOOL CALLS:", message.tool_calls)
        print("==============================")

        if not message.tool_calls:

            assistant_message = ConversationMessage(
                conversation_id = conversation_id,
                role = "assistant",
                content = message.content or "",
            )

            db.add(assistant_message)

            await db.commit()

            print("======== SAVED ASSISTANT TOOL CALLS ========")
            print(assistant_message.tool_calls)
            print("============================================")

            return {
                "message": assistant_message.content,
            }

        assistant_tool_calls = [
            tool_call.model_dump(
                exclude_none=True,
            )
            for tool_call in message.tool_calls
        ]

        assistant_message = ConversationMessage(
            conversation_id=conversation_id,
            role="assistant",
            content=message.content,
            tool_calls=json.dumps(assistant_tool_calls),
        )

        db.add(assistant_message)

        await db.commit()

        messages.append(
            {
                "role" : "assistant",
                "content" : message.content ,
                "tool_calls" : assistant_tool_calls,
            }
        )

        for tool_call in message.tool_calls:

            tool_name = tool_call.function.name

            arguments = json.loads(tool_call.function.arguments)

            selected_tool = next(
                (
                    tool
                    for tool in selected_tools
                    if tool.name == tool_name
                ),
                None,
            )

            if not selected_tool:

                messages.append(
                    {
                        "role" : "tool",
                        "tool_call_id" : tool_call.id,
                        "content": (
                            f"Tool '{tool_name}' "
                            "is not selected for this agent"
                        ),
                    }
                )
                continue

            server = await db.get(MCPServer, selected_tool.mcp_server_id)

            if not server:

                messages.append(
                    {
                        "role" : "tool",
                        "tool_call_id" : tool_call.id,
                        "content": (
                            "MCP server not found"
                        ),
                    }
                )
                continue

            client = MCPClient()
            test_token = os.getenv("THY_TEST_ACCESS_TOKEN")

            try:
                await client.connect(
                    server.url,
                    access_token=x_mcp_token or test_token,
                )

                tool_result = await client.call_tool(tool_name, arguments)

                tool_text = ""

                if tool_result.content:
                    for content in tool_result.content:
                        if hasattr(content, "text"):
                            tool_text += content.text

                if not tool_text:
                    tool_text = str(tool_result)

                tool_message = ConversationMessage(
                    conversation_id = conversation_id,
                    role = "tool",
                    content = tool_text,
                    tool_name = tool_name,
                    tool_call_id = tool_call.id,
                    tool_arguments = json.dumps(arguments),
                )

                db.add(tool_message)

                await db.commit()

                messages.append(
                    {
                        "role" : "tool",
                        "tool_call_id" : tool_call.id,
                        "content": tool_text
                    }
                )


            except Exception as exc:

                error_text = (
                    f"Failed to execute MCP tool: {str(exc)}"
                )

                error_tool_message = ConversationMessage(
                    conversation_id=conversation_id,
                    role="tool",
                    content=error_text,
                    tool_name=tool_name,
                    tool_call_id=tool_call.id,
                    tool_arguments=json.dumps(arguments),
                )

                db.add(error_tool_message)
                await db.commit()

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": error_text,
                    }
                )


            finally:
                try:
                    await client.close()
                except BaseException as exc:
                    print("MCP FINALIZE ERROR:", repr(exc))

    raise HTTPException(
        status_code=500,
        detail=(
            "Agent reached maximum "
            "tool-calling iterations"
        ),
    )



@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
        conversation_id: int,
        db: AsyncSession = Depends(get_db),
):
    conversation = await db.get(Conversation, conversation_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    result = await db.scalars(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation.id)
        .order_by(ConversationMessage.id.asc())
    )

    return result.all()