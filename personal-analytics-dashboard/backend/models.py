from sqlalchemy import Column, Integer, String, DateTime, Boolean
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    bio = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)

    duration_minutes = Column(Integer, default=30)
    # deadline stored as ISO string for simplicity in early MVP
    deadline = Column(String(50), nullable=True)

    importance = Column(Integer, default=3)  # 1-5
    completed = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(10), nullable=False)      # YYYY-MM-DD
    stress_level = Column(Integer, nullable=False)  # 1-5
    notes = Column(String(1000), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
