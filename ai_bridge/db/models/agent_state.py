from sqlalchemy import String, DateTime, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from ai_bridge.db.base import Base
class AgentState(Base):
    __tablename__ = "agent_states"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[str] = mapped_column(String)
    parent_agent_id: Mapped[str | None] = mapped_column(String, nullable=True)
    role: Mapped[str] = mapped_column(String)
    capabilities_json: Mapped[dict] = mapped_column(JSON)
    state_json: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
