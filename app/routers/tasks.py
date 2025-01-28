from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app import models, schemas
from datetime import datetime, timedelta, timezone
from typing import List
from app.utils.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=schemas.TaskResponse)
async def create_task(
    task: schemas.TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Create a new task.
    """
    
    try:
        new_task = models.Task(
            name=task.name,
            description=task.description,
            due_date=task.due_date,
            assigned_to=task.assigned_to,
            priority=task.priority,
        )
        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)
        return new_task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}"
                            ) from e

@router.get("/", response_model=List[schemas.TaskResponse])
async def list_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
   Get all the task posted by the user.
    """
    
    try:
        result = await db.execute(select(models.Task))
        # tasks = 
        return result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tasks: {str(e)}"
                            ) from e

@router.get("/{task_id}", response_model=schemas.TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    
    """
   Get the task posted by the user by taskid.
    """
    try:
        result = await db.execute(select(models.Task).filter(models.Task.task_id == task_id))
        if task := result.scalars().first():
            return task
        else:
            raise HTTPException(status_code=404, detail="Task not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching task: {str(e)}"
                            ) from e

@router.put("/{task_id}", response_model=schemas.TaskResponse)
async def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Update many fields of a specific task.
    """
    
    try:
        result = await db.execute(select(models.Task).filter(models.Task.task_id == task_id))
        task = result.scalars().first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        update_data = task_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task, key, value)

        if task.status == "completed" and not task.completed_date:
            task.completed_date = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(task)
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating task: {str(e)}"
                            ) from e

@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    
    """
    Delete a specific task by task id.
    """
    try:
        result = await db.execute(select(models.Task).filter(models.Task.task_id == task_id))
        task = result.scalars().first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        await db.delete(task)
        await db.commit()
        return {"detail": "Task deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting task: {str(e)}"
                            ) from e

@router.post("/{task_id}/schedule")
async def schedule_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    
    """
    Schedule new task.
    """
    try:
        result = await db.execute(select(models.Task).filter(models.Task.task_id == task_id))
        task = result.scalars().first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if not task.due_date:
            raise HTTPException(status_code=400, detail="Task has no due date")

        reminder_time = task.due_date - timedelta(hours=1)
        background_tasks.add_task(send_reminder, task.name, reminder_time)
        return {"detail": "Reminder scheduled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scheduling reminder: {str(e)}"
                            ) from e

@router.patch("/{task_id}/status", response_model=schemas.TaskResponse)
async def update_task_status(
    task_id: int,
    status_update: schemas.UpdateStatusRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Update the status of a specific task.
    """
    try:
        result = await db.execute(select(models.Task).filter(models.Task.task_id == task_id))
        task = result.scalars().first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        try:
            task.update_status(models.TaskStatus(status_update.status))
            if task.status == "completed" and not task.completed_date:
                task.completed_date = datetime.now(timezone.utc)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status value") from e

        await db.commit()
        await db.refresh(task)
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating task status: {str(e)}") from e

@router.patch("/{task_id}/due_date", response_model=schemas.TaskResponse)
async def update_task_due_date(
    task_id: int,
    new_due_date_update: schemas.UpdateNewDueDateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Update the due date of a specific task.
    """
    try:
        result = await db.execute(select(models.Task).filter(models.Task.task_id == task_id))
        task = result.scalars().first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found") 

        task.update_due_date(new_due_date_update.due_date)

        await db.commit()
        await db.refresh(task)
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating task due date: {str(e)}") from e
async def send_reminder(task_name: str, reminder_time: datetime):
    try:
        print(f"Reminder: Task '{task_name}' is due at {reminder_time}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending reminder: {str(e)}") from e
