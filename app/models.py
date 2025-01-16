from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import enum
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class TaskStatus(str, enum.Enum): #Enumeration for symbolic names
    pending = "pending"
    in_progress = "in-progress"
    completed = "completed"
    overdue = "overdue"

class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.pending)
    due_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    assigned_to = Column(String, nullable=True)
    priority = Column(String, nullable=False, default="medium")
    creation_time = Column(DateTime, default=datetime.utcnow, nullable=False)

    def update_status(self, status: TaskStatus):
        self.status = status

    def update_due_date(self, new_due_date):
        self.due_date = new_due_date
        
class TelegramSubscriber(Base):
    __tablename__ = "telegram_subscribers"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, unique=True, index=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)