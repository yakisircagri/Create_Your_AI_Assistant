from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

class MCPConnection(Base):
    __tablename__ = "mcp_connection"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "mcp_server_id",
            name="uq_user_mcp_server_connection",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    mcp_server_id: Mapped[int] = mapped_column(
        ForeignKey("mcp_servers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    access_token: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    refresh_token: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    token_type: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    scope: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="connected",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="mcp_connections",
    )
    
    oauth_state: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    code_verifier: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    mcp_server = relationship(
        "MCPServer",
    )

