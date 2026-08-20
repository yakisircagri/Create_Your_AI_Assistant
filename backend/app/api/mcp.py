from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.models.mcp_server import MCPServer
from app.models.mcp_tools import MCPTool
from app.schemas.mcp import (
    MCPServerCreate,
    MCPServerResponse,
)
from app.services.mcp.client import MCPClient



router = APIRouter(
    prefix="/api/mcp",
    tags=["MCP"],
)



@router.post("/register", response_model=MCPServerResponse)
async def register_mcp_server(
        data: MCPServerCreate,
        db : AsyncSession = Depends(get_db),
):
    existing_server = await db.scalar(
        select(MCPServer).where(
            MCPServer.url == data.url
        )
    )

    if existing_server:
        raise HTTPException(
            status_code=400,
            detail="Server with this url already exists",
        )

    server = MCPServer(
        name=data.name,
        url=data.url,
        description=data.description,
    )

    db.add(server)

    await db.commit()
    await db.refresh(server)

    return server



@router.post("/discover")
async def discover_mcp_server(
    server_id: int,
    x_mcp_token: str | None = Header(
        default=None,
        alias="X-MCP-Token",
    ),
    db: AsyncSession = Depends(get_db),
):
    server = await db.get(MCPServer, server_id)

    if not server:
        raise HTTPException(
            status_code=404,
            detail="MCP server not found",
        )

    client = MCPClient()

    try:

        tools_result = await client.connect(
            server.url,
            access_token=x_mcp_token,
        )

        discovered_tools = []

        for tool in tools_result.tools:

            existing_tool = await db.scalar(
                select(MCPTool).where(
                    MCPTool.mcp_server_id == server.id,
                    MCPTool.name == tool.name,
                )
            )

            if existing_tool:
                existing_tool.description = tool.description
                existing_tool.input_schema = tool.input_schema

                discovered_tools.append(existing_tool)

            else:
                mcp_tool = MCPTool(
                    mcp_server_id=server.id,
                    name=tool.name,
                    description=tool.description,
                    input_schema=tool.input_schema,
                )

                db.add(mcp_tool)

                await db.flush()

                discovered_tools.append(mcp_tool)

        await db.commit()

        return {
            "server_id": server.id,
            "server_name": server.name,
            "tools": [
                {
                    "id": tool.id,
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                }
                for tool in discovered_tools
            ],
        }

    except Exception as exc:
        await db.rollback()

        print("MCP DISCOVER ERROR:", repr(exc))

        raise HTTPException(
            status_code=502,
            detail=f"Failed to discover MCP server: {str(exc)}",
        )

    finally:
        await client.close()



@router.get("", response_model=list[MCPServerResponse])
async def get_mcp_servers(
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(MCPServer).order_by(MCPServer.id.desc())

    if search:
        query = query.where(
            MCPServer.name.ilike(f"%{search}%")
        )

    result = await db.scalars(query)

    return result.all()





