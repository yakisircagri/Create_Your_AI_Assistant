from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base

class MCPServer(Base):

    __tablename__ = "mcp_servers"

    id : Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    name : Mapped[str] = mapped_column(
        String(255),
        nullable = False,
    )

    url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        unique=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )