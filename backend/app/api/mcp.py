from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.models.mcp_tools import MCPTool
from app.schemas.mcp import (
    MCPServerCreate,
    MCPServerResponse,
)
from app.services.mcp.client import MCPClient
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from app.models.mcp_connection import MCPConnection
from app.models.mcp_server import MCPServer
from app.services.mcp.connections.registry import get_connection_provider
from app.core.security import get_current_user
from app.models.users import User



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
    current_user: User = Depends(get_current_user),
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
        access_token = None

        if server.connection_provider:
            connection = await db.scalar(
                select(MCPConnection).where(
                    MCPConnection.user_id == current_user.id,
                    MCPConnection.mcp_server_id == server.id,
                )
            )

            if not connection:
                return {
                    "server_id": server.id,
                    "server_name": server.name,
                    "connected": False,
                    "auth_required": True,
                    "connect_url": None,
                    "tools": [],
                }

            provider = get_connection_provider(
                server.connection_provider
            )

            if not provider:
                raise HTTPException(
                    status_code=500,
                    detail=(
                        f"Connection provider not found: "
                        f"{server.connection_provider}"
                    ),
                )

            try:
                access_token = await provider.get_valid_access_token(
                    connection=connection,
                    server=server,
                    db=db,
                )

            except Exception as exc:
                print("MCP CONNECTION ERROR:", repr(exc))

                return {
                    "server_id": server.id,
                    "server_name": server.name,
                    "connected": False,
                    "auth_required": True,
                    "connect_url": None,
                    "tools": [],
                }

        tools_result = await client.connect(
            server.url,
            access_token=access_token,
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
            "connected": True,
            "auth_required": bool(server.connection_provider),
            "connect_url": None,
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

    except HTTPException:
        raise

    except Exception as exc:
        await db.rollback()

        print("MCP DISCOVER ERROR:", repr(exc))

        raise HTTPException(
            status_code=502,
            detail=f"Failed to discover MCP server: {str(exc)}",
        )

    finally:
        try:
            await client.close()
        except BaseException as exc:
            print("MCP FINALIZE ERROR:", repr(exc))


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



@router.post("/{server_id}/connect")
async def connect_mcp_server(
    server_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    server = await db.get(
        MCPServer,
        server_id,
    )

    if not server:
        raise HTTPException(
            status_code=404,
            detail="MCP server not found",
        )

    if not server.connection_provider:
        raise HTTPException(
            status_code=400,
            detail=(
                "This MCP server does not "
                "require authentication"
            ),
        )

    existing_connection = await db.scalar(
        select(MCPConnection).where(
            MCPConnection.user_id == current_user.id,
            MCPConnection.mcp_server_id == server.id,
        )
    )

    if (
        existing_connection
        and existing_connection.status == "connected"
    ):
        return {
            "connected": True,
            "authorization_url": None,
            "connection_id": existing_connection.id,
        }

    provider = get_connection_provider(
        server.connection_provider
    )

    if not provider:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Connection provider "
                f"'{server.connection_provider}' "
                f"is not registered"
            ),
        )

    authorization_url = await provider.start_connection(
        user_id=current_user.id,
        server=server,
        db=db,
    )

    return {
        "connected": False,
        "authorization_url": authorization_url,
    }


@router.get("/oauth/callback")
async def mcp_oauth_callback(
        code: str,
        state: str,
        db: AsyncSession = Depends(get_db),
):
    connection = await db.scalar(
        select(MCPConnection).where(
            MCPConnection.oauth_state == state,
        )
    )

    if not connection:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OAuth state",
        )

    server = await db.get(MCPServer, connection.mcp_server_id)

    if not server:
        raise HTTPException(
            status_code=404,
            detail="MCP server not found",
        )

    provider = get_connection_provider(server.connection_provider)

    if not provider:
        raise HTTPException(
            status_code=400,
            detail="Connection provider not found",
        )

    connection = await provider.complete_connection(
        connection=connection,
        server=server,
        code=code,
        state=state,
        db=db,
    )

    return {
        "message": "MCP server connected successfully",
        "connection_id": connection.id,
        "server_id": connection.mcp_server_id,
        "status": connection.status,
    }






