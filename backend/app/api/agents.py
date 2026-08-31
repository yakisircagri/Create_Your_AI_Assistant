from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.dependencies import get_db

from app.models.users import User
from app.models.agent import Agent
from app.models.agent_tool import AgentTool
from app.models.mcp_connection import MCPConnection
from app.models.mcp_server import MCPServer
from app.models.mcp_tools import MCPTool

from app.schemas.agent import (
    AgentCreate,
    AgentResponse,
    AgentToolSelect,
    AgentToolCallRequest,
    AgentToolResponse,
)

from app.services.mcp.client import MCPClient
from app.services.mcp.connections.registry import get_connection_provider

router = APIRouter(
    prefix="/api/agents",
    tags=["Agents"],
)


@router.post("", response_model=AgentResponse)
async def create_agent(
        data: AgentCreate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    agent = Agent(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        system_prompt=data.system_prompt,
        model=data.model,
    )

    db.add(agent)

    await db.commit()
    await db.refresh(agent)

    return agent



@router.get("", response_model=list[AgentResponse])
async def get_agents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.scalars(
        select(Agent)
        .where(Agent.user_id == current_user.id)
        .order_by(Agent.id.desc())
    )

    return result.all()



@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await db.scalar(
        select(Agent).where(
            Agent.id == agent_id,
            Agent.user_id == current_user.id,
        )
    )

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    return agent



@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await db.scalar(
        select(Agent).where(
            Agent.id == agent_id,
            Agent.user_id == current_user.id,
        )
    )

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    await db.delete(agent)
    await db.commit()

    return {
        "message": "Agent deleted successfully",
    }



@router.post("/{agent_id}/tools")
async def select_agent_tools(
    agent_id: int,
    data: AgentToolSelect,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await db.scalar(
        select(Agent).where(
            Agent.id == agent_id,
            Agent.user_id == current_user.id,
        )
    )

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    tool_ids = list(set(data.tool_ids))

    if tool_ids:
        result = await db.scalars(
            select(MCPTool).where(
                MCPTool.id.in_(tool_ids)
            )
        )

        tools = result.all()

        if len(tools) != len(tool_ids):
            raise HTTPException(
                status_code=404,
                detail="One or more MCP tools not found",
            )

    existing_tools = await db.scalars(
        select(AgentTool).where(
            AgentTool.agent_id == agent_id
        )
    )

    for agent_tool in existing_tools.all():
        await db.delete(agent_tool)

    for tool_id in tool_ids:
        db.add(
            AgentTool(
                agent_id=agent_id,
                mcp_tool_id=tool_id,
                enabled=True,
            )
        )

    await db.commit()

    return {
        "message": "Agent tools updated successfully",
        "agent_id": agent_id,
        "tool_ids": tool_ids,
    }



@router.get(
    "/{agent_id}/tools",
    response_model=list[AgentToolResponse],
)
async def get_agent_tools(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await db.scalar(
        select(Agent).where(
            Agent.id == agent_id,
            Agent.user_id == current_user.id,
        )
    )

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    result = await db.scalars(
        select(MCPTool)
        .join(
            AgentTool,
            AgentTool.mcp_tool_id == MCPTool.id,
        )
        .where(
            AgentTool.agent_id == agent_id
        )
        .order_by(MCPTool.id)
    )

    return result.all()



@router.post("/{agent_id}/tools/{tool_id}/call")
async def call_agent_tool(
    agent_id: int,
    tool_id: int,
    data: AgentToolCallRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await db.scalar(
        select(Agent).where(
            Agent.id == agent_id,
            Agent.user_id == current_user.id,
        )
    )

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    result = await db.execute(
        select(MCPTool, MCPServer)
        .join(
            MCPServer,
            MCPServer.id == MCPTool.mcp_server_id,
        )
        .join(
            AgentTool,
            AgentTool.mcp_tool_id == MCPTool.id,
        )
        .where(
            AgentTool.agent_id == agent_id,
            AgentTool.mcp_tool_id == tool_id,
        )
    )

    row = result.first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Tool is not selected for this agent",
        )

    tool, server = row

    client = MCPClient()

    try:
        access_token = None

        if server.connection_provider:
            connection = await db.scalar(
                select(MCPConnection).where(
                    MCPConnection.user_id == current_user.id,
                    MCPConnection.mcp_server_id == server.id,
                )
            )

            if not connection:
                raise HTTPException(
                    status_code=401,
                    detail="User is not connected to this MCP server",
                )

            provider = get_connection_provider(
                server.connection_provider
            )

            if not provider:
                raise HTTPException(
                    status_code=500,
                    detail="Connection provider not found",
                )

            access_token = await provider.get_valid_access_token(
                connection=connection,
                server=server,
                db=db,
            )

        tools_result = await client.connect(
            server.url,
            access_token=access_token,
        )

        available_tool = next(
            (
                item
                for item in tools_result.tools
                if item.name == tool.name
            ),
            None,
        )

        if not available_tool:
            raise HTTPException(
                status_code=404,
                detail="Tool not found on MCP server",
            )

        tool_result = await client.call_tool(
            tool.name,
            data.arguments,
        )

        return {
            "agent_id": agent_id,
            "tool_id": tool_id,
            "tool_name": tool.name,
            "result": tool_result.model_dump(),
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to execute MCP tool: {str(exc)}",
        )

    finally:
        try:
            await client.close()
        except BaseException as exc:
            print("MCP FINALIZE ERROR:", repr(exc))



@router.delete("/{agent_id}/tools/{tool_id}")
async def delete_agent_tool(
    agent_id: int,
    tool_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent = await db.scalar(
        select(Agent).where(
            Agent.id == agent_id,
            Agent.user_id == current_user.id,
        )
    )

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    agent_tool = await db.scalar(
        select(AgentTool).where(
            AgentTool.agent_id == agent_id,
            AgentTool.mcp_tool_id == tool_id,
        )
    )

    if not agent_tool:
        raise HTTPException(
            status_code=404,
            detail="Tool is not selected for this agent",
        )

    await db.delete(agent_tool)
    await db.commit()

    return {
        "message": "Tool removed from agent successfully",
        "agent_id": agent_id,
        "tool_id": tool_id,
    }



