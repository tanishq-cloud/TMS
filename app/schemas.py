from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime]= None
    assigned_to: Optional[str] = None
    priority: Optional[str] = Field(default="medium", pattern="^(low|medium|high)$")

class TaskResponse(BaseModel):
    task_id: int
    name: str
    description: Optional[str]
    status: str
    due_date: Optional[datetime]
    completed_date: Optional[datetime]
    assigned_to: Optional[str]
    priority: str
    creation_time: datetime     

    class Config:
        orm_mode = True

class UpdateStatusRequest(BaseModel):
    status: str

class UpdateNewDueDateRequest(BaseModel):
    due_date: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

class Event(BaseModel):
    type: str
    message: str

    class Config:
        orm_mode = True
        
