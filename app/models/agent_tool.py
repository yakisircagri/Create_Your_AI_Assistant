from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, Relationship

from app.db.session import Base



class AgentTool(Base):
    __tablename__ = "agent_tools"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    agent_id: Mapped[int] = mapped_column(
        ForeignKey("agents.id",ondelete="CASCADE"),
        nullable=False,
    )

    mcp_tool_id: Mapped[int] = mapped_column(
        ForeignKey("mcp_tools.id",ondelete="CASCADE"),
        nullable=False,
    )

    enabled: Mapped[bool] = mapped_column(
        default= True,
        nullable=False,
    )

    agent = relationship(
        "Agent",
        back_populates="tools",
    )

    mcp_tool = relationship(
        "MCPTool",
    )


