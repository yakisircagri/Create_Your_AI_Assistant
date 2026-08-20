from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

class Agent(Base):
    __tablename__ = 'agents'

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(250),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable= True,
    )

    system_prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable= True,
    )

    model: Mapped[str] = mapped_column(
        String(100),
        nullable= False,
        default="gpt-5.2"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default= datetime.utcnow(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default= datetime.utcnow(),
        onupdate=datetime.utcnow(),
    )

    tools = relationship(
        "AgentTool",
        back_populates="agent",
        cascade= "all, delete-orphan"
    )

    conversations = relationship(
        "Conversation",
        back_populates="agent",
        cascade="all, delete-orphan",
    )