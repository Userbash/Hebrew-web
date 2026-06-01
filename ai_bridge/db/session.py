from __future__ import annotations
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
DB_URL = os.getenv("AI_BRIDGE_MEMORY_DATABASE_URL", "")
engine = create_async_engine(DB_URL, echo=False) if DB_URL else None
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False) if engine else None
