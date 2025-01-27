from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import csv
from io import StringIO
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
from app.database import get_db
from app.utils.auth import get_current_user
from app import models
import pandas as pd
from datetime import datetime

router = APIRouter()

@router.get("/clean")
async def clean_data(db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    
    result = await db.execute(select(models.Task))
    tasks = result.scalars().all()

    if not tasks:
        return {"message": "No tasks found"}

    
    task_data = [
        {
            "task_id": task.task_id,
            "name": task.name,
            "description": task.description,
            "due_date": task.due_date,
            "completed_date": task.completed_date,
            "status": task.status,
            "assigned_to": task.assigned_to,
            "priority": task.priority
        }
        for task in tasks
    ]
    df = pd.DataFrame(task_data)

    
    df = df.drop_duplicates(subset=["task_id", "assigned_to"])
    df["due_date"] = pd.to_datetime(df["due_date"], errors="coerce")
    df["completed_date"] = pd.to_datetime(df["completed_date"], errors="coerce")
    df["status"] = df["completed_date"].apply(
        lambda x: "completed" if pd.notnull(x) else "pending"
    )

    
    await db.execute(text("DELETE FROM tasks"))  
    for _, row in df.iterrows():
        new_task = models.Task(
            task_id=row["task_id"],
            name=row["name"],
            description=row["description"],
            due_date=row["due_date"] if pd.notnull(row["due_date"]) else None,
            completed_date=row["completed_date"] if pd.notnull(row["completed_date"]) else None,
            status=row["status"],
            assigned_to=row["assigned_to"],
            priority=row["priority"]
        )
        db.add(new_task)

    await db.commit()
    return {"message": "Data cleaned successfully"}


@router.get("/overdue")
async def analyze_overdue(db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    
    result = await db.execute(select(models.Task))
    tasks = result.scalars().all()

    if not tasks:
        return {"overdue_tasks": 0, "total_tasks": 0}

   
    task_data = [
        {
            "task_id": task.task_id,
            "due_date": task.due_date,
            "completed_date": task.completed_date,
            "status": task.status,
        }
        for task in tasks
    ]
    df = pd.DataFrame(task_data)

    
    df["due_date"] = pd.to_datetime(df["due_date"], errors="coerce")
    df["completed_date"] = pd.to_datetime(df["completed_date"], errors="coerce")
    df["overdue"] = df.apply(
        lambda row: pd.notnull(row["due_date"]) and pd.notnull(row["completed_date"]) and row["due_date"] < row["completed_date"],
        axis=1
    )
    
    overdue_count = int(df["overdue"].sum())
    completed_count = int(df["status"].eq('completed').sum())


    return {
        "completed_count": completed_count,
        "overdue_tasks": overdue_count,
        "total_tasks": len(df)
    }


@router.get("/completion-time")
async def analyze_completion_time(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    
    result = await db.execute(select(models.Task))
    tasks = result.scalars().all()

    if not tasks:
        return {"average_completion_time": None}

    
    task_data = [
        {
            "task_id": task.task_id,
            "creation_time": task.creation_time,
            "completed_date": task.completed_date,
        }
        for task in tasks
    ]
    df = pd.DataFrame(task_data)

    
    df["creation_time"] = pd.to_datetime(df["creation_time"], errors="coerce")
    df["completed_date"] = pd.to_datetime(df["completed_date"], errors="coerce")
    df["completion_time"] = df.apply(
        lambda row: (row["completed_date"] - row["creation_time"]).days
        if pd.notnull(row["creation_time"]) and pd.notnull(row["completed_date"])
        else None,
        axis=1
    )
    avg_completion_time = df["completion_time"].mean()

    return {"average_completion_time": avg_completion_time}



@router.get("/download-tasks-csv")
async def download_tasks_csv(db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    
    result = await db.execute(select(models.Task))
    tasks = result.scalars().all()
    tasks = sorted(tasks, key=lambda task: task.task_id)

    if not tasks:
        raise HTTPException(status_code=404, detail="No tasks found")

    
    csv_file = StringIO()
    csv_writer = csv.writer(csv_file)

    
    headers = ["task_id", "name", "description", "due_date", "completed_date", "status", "assigned_to", "priority"]
    csv_writer.writerow(headers)

    
    for task in tasks:
        csv_writer.writerow([
            task.task_id,
            task.name,
            task.description,
            task.due_date.strftime("%Y-%m-%d %H:%M:%S") if task.due_date else "",
            task.completed_date.strftime("%Y-%m-%d %H:%M:%S") if task.completed_date else "",
            task.status,
            task.assigned_to,
            task.priority,
        ])

    csv_file.seek(0)

    
    return StreamingResponse(
        csv_file,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=tasks.csv"},
    )

