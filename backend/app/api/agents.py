import json

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.models.agent import Agent
from app.models.agent_tool import AgentTool
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

router = APIRouter(
    prefix="/api/agents",
    tags=["Agents"],
)


@router.post("", response_model=AgentResponse)
async def create_agent(
        data: AgentCreate,
        db: AsyncSession = Depends(get_db),
):
    agent = Agent(
        name=data.name,
        description=data.description,
        system_prompt=data.system_prompt,
        model=data.model,
    )

    db.add(agent)

    await db.commit()
    await db.refresh(agent)

    return agent



@router.get("", response_model= list[AgentResponse])
async def get_agents(db: AsyncSession = Depends(get_db)):

    result = await db.scalars(
        select(Agent).order_by(Agent.id.desc())
    )

    return result.all()



@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: int, db: AsyncSession = Depends(get_db)):

    agent = await db.get(Agent, agent_id)

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    return agent



@router.delete("/{agent_id}")
async def delete_agent(agent_id: int, db: AsyncSession = Depends(get_db)):

    agent = await db.get(Agent, agent_id)

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
        db: AsyncSession = Depends(get_db),
):
    agent = await db.get(Agent, agent_id)

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    if not data.tool_ids:
        raise HTTPException(
            status_code=400,
            detail="At least one tool must be selected",
        )

    result = await db.scalars(
        select(MCPTool).where(
            MCPTool.id.in_(data.tool_ids)
        )
    )

    tools = result.all()

    if len(tools) != len(set(data.tool_ids)):
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

    for tool_id in set(data.tool_ids):
        agent_tool = AgentTool(
            agent_id=agent_id,
            mcp_tool_id= tool_id,
            enabled=True
        )

        db.add(agent_tool)

    await db.commit()

    return {
        "message": "Agent tools updated successfully",
        "agent_id": agent_id,
        "tool_ids": list(set(data.tool_ids)),
    }



@router.get("/{agent_id}/tools", response_model= list[AgentToolResponse])
async def get_agent_tools(agent_id: int, db: AsyncSession = Depends(get_db)):

    agent = await db.get(Agent, agent_id)

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    result = await db.scalars(
        select(MCPTool).join(
            AgentTool,
            AgentTool.mcp_tool_id== MCPTool.id,
        ).where(
            AgentTool.agent_id == agent_id
        ).order_by(MCPTool.id)
    )

    return result.all()



@router.post("/{agent_id}/tools/{tool_id}/call")
async def call_agent_tool(
        agent_id: int,
        tool_id: int,
        data: AgentToolCallRequest,
        x_mcp_token: str | None = Header(
            default=None,
            alias="X-MCP-Token",
        ),
        db: AsyncSession = Depends(get_db),
):
    agent = await db.get(Agent, agent_id)

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    result = await db.execute(
        select(MCPTool,MCPServer).join(
            MCPServer,
            MCPServer.id == MCPTool.mcp_server_id
        ).join(
            AgentTool,
            AgentTool.mcp_tool_id == MCPTool.id,
        ).where(
            AgentTool.agent_id == agent_id,
            AgentTool.mcp_tool_id == tool_id
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
        print("X MCP TOKEN EXISTS:", bool(x_mcp_token))

        result = await client.connect(
            server.url,
            access_token=x_mcp_token,
        )

        available_tool = next(
            (
                item
                for item in result.tools
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

    except HTTPException :
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to execute MCP tool: {str(exc)}",
        )

    finally:
        await client.close()



@router.delete("/{agent_id}/tools/{tool_id}")
async def delete_agent_tool(
        agent_id: int,
        tool_id: int,
        db: AsyncSession = Depends(get_db),
):
    agent = await db.get(Agent, agent_id)

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="Agent not found",
        )

    result = await db.execute(
        select(AgentTool).where(
            AgentTool.agent_id == agent_id,
            AgentTool.mcp_tool_id == tool_id,
        )
    )

    agent_tool = result.scalar_one_or_none()

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



