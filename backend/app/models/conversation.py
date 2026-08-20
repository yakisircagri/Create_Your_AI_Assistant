from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.session import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id : Mapped[int] = mapped_column(
        primary_key = True,
        index = True,
    )

    agent_id : Mapped[int] = mapped_column(
        ForeignKey("agents.id",ondelete="CASCADE"),
        nullable = False,
        index = True,
    )

    title : Mapped[str | None] = mapped_column(
        String(255),
        nullable = True,
    )

    created_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default = func.now(),
        nullable = False,
    )

    updated_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate = func.now(),
        nullable = False,
    )

    agent = relationship("Agent", back_populates="conversations")

    messages = relationship(
        "ConversationMessage",
        back_populates="conversation",
        cascade = "all, delete-orphan",
        order_by = "ConversationMessage.id",
    )