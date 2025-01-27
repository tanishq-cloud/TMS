from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from fastapi.responses import StreamingResponse
from app.utils.auth import get_current_user
from app import models

router = APIRouter()


async def get_task_data(db: AsyncSession):
    """Fetch all task data asynchronously from the database."""
    query = text("SELECT * FROM tasks")
    result = await db.execute(query)
    rows = result.fetchall()

    # Convert to pandas DataFrame
    df = pd.DataFrame(rows, columns=result.keys())
    return df


def save_plot_to_stream():
    """Save the current Matplotlib figure to a BytesIO stream."""
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    plt.close()
    return buffer


@router.get("/completed-tasks-per-day")
async def completed_tasks_per_day(
    db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    df = await get_task_data(db)
    df["completed_date"] = pd.to_datetime(df["completed_date"])
    df["completion_date"] = df["completed_date"].dt.date
    completion_count = df.groupby("completion_date").size()

    plt.figure(figsize=(10, 6))
    completion_count.plot(kind="bar", color="skyblue")
    plt.title("Completed Tasks Per Day")
    plt.xlabel("Date")
    plt.ylabel("Number of Completed Tasks")
    plt.xticks(rotation=0)

    buffer = save_plot_to_stream()
    return StreamingResponse(buffer, media_type="image/png")


@router.get("/task-priority-distribution")
async def task_priority_distribution(
    db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    df = await get_task_data(db)

    priority_counts = df["priority"].value_counts()

    plt.figure(figsize=(8, 8))
    priority_counts.plot(
        kind="pie", autopct="%1.1f%%", startangle=90, colors=["#ff9999", "#66b3ff", "#99ff99"]
    )
    plt.title("Task Priority Distribution")
    plt.ylabel("")

    buffer = save_plot_to_stream()
    return StreamingResponse(buffer, media_type="image/png")


@router.get("/completion-trends")
async def completion_trends(
    db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    df = await get_task_data(db)
    df["completed_date"] = pd.to_datetime(df["completed_date"])
    df["completion_date"] = df["completed_date"].dt.date

    completion_count = df.groupby("completion_date").size()

    plt.figure(figsize=(10, 6))
    ax = sns.lineplot(x=completion_count.index, y=completion_count.values)
    plt.title("Completion Trends Over Time")
    plt.xlabel("Date")
    plt.ylabel("Number of Completed Tasks")
    plt.xticks(rotation=45)
    
    for x, y in zip(completion_count.index, completion_count.values):
        ax.text(x, y, str(y),
        fontsize=11, ha='right')

    buffer = save_plot_to_stream()
    return StreamingResponse(buffer, media_type="image/png")


@router.get("/time-vs-priority")
async def time_vs_priority(
    db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    df = await get_task_data(db)
    df["completed_date"] = pd.to_datetime(df["completed_date"])
    df["due_date"] = pd.to_datetime(df["due_date"])
    df["time_to_complete"] = (df["completed_date"] - df["due_date"]).dt.days

    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x="time_to_complete", y="priority", hue="priority", palette="Set2")
    plt.title("Time to Complete Tasks vs Priority")
    plt.xlabel("Days to Complete")
    plt.ylabel("Priority")

    buffer = save_plot_to_stream()
    return StreamingResponse(buffer, media_type="image/png")
