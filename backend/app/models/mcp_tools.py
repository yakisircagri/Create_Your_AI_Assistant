from sqlalchemy import ForeignKey, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.db.session import Base



class MCPTool(Base):

    __tablename__ = "mcp_tools"

    id : Mapped[int] = mapped_column(
        primary_key = True,
        autoincrement = True,
    )

    mcp_server_id : Mapped[int] = mapped_column(
        ForeignKey("mcp_servers.id", ondelete="CASCADE"),
        nullable=False,
    )

    name : Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description : Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    input_schema: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

