from sqlalchemy import Column, Integer, String, DateTime, Boolean
from database import Base
from datetime import datetime

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)

    duration_minutes = Column(Integer, default=30)
    # deadline stored as ISO string for simplicity in early MVP
    deadline = Column(String, nullable=True)

    importance = Column(Integer, default=3)  # 1-5
    completed = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, nullable=False)      # YYYY-MM-DD
    stress_level = Column(Integer, nullable=False)  # 1-5
    notes = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
