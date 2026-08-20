from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id : Mapped[int] = mapped_column(
        primary_key = True,
        index = True,
    )

    conversation_id : Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable = False,
        index = True,
    )

    role : Mapped[str] = mapped_column(
        String(50),
        nullable = False,
    )

    content : Mapped[str | None] = mapped_column(
        Text,
        nullable = True,
    )

    tool_name : Mapped[str | None] = mapped_column(
        String(255),
        nullable = True,
    )

    tool_call_id : Mapped[str | None] = mapped_column(
        String(255),
        nullable = True,
    )

    tool_arguments : Mapped[str | None] = mapped_column(
        Text,
        nullable = True,
    )

    tool_calls: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable = False,
    )

    conversation = relationship(
        "Conversation",
        back_populates="messages",
    )