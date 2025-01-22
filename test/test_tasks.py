import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from app.main import app  # Assuming the FastAPI app is defined in `main.py`
from app.database import get_db
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Base
from app.utils.auth import create_access_token

# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Dependency override for the database
async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

# Mock user setup
MOCK_USER = {"username": "testuser", "id": 1}
MOCK_TOKEN = create_access_token({"sub": MOCK_USER["username"]})

@pytest.fixture(autouse=True, scope="module")
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# Helper function to include headers
def auth_headers():
    return {"Authorization": f"Bearer {MOCK_TOKEN}"}

@pytest.mark.asyncio
async def test_create_task():
    async with AsyncClient(app=app, base_url="http://test") as client:
        task_data = {
            "name": "Test Task",
            "description": "A test task description",
            "due_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "assigned_to": MOCK_USER["id"],
            "priority": "high",
        }
        response = await client.post("/tasks/", json=task_data, headers=auth_headers())
        assert response.status_code == 200
        assert response.json()["name"] == "Test Task"

@pytest.mark.asyncio
async def test_list_tasks():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/tasks/", headers=auth_headers())
        assert response.status_code == 200
        assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_task():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create a task to fetch
        task_data = {
            "name": "Fetchable Task",
            "description": "Another task description",
            "due_date": (datetime.utcnow() + timedelta(days=2)).isoformat(),
            "assigned_to": MOCK_USER["id"],
            "priority": "medium",
        }
        create_response = await client.post("/tasks/", json=task_data, headers=auth_headers())
        task_id = create_response.json()["task_id"]

        # Fetch the task
        response = await client.get(f"/tasks/{task_id}", headers=auth_headers())
        assert response.status_code == 200
        assert response.json()["name"] == "Fetchable Task"

@pytest.mark.asyncio
async def test_update_task():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create a task to update
        task_data = {
            "name": "Updatable Task",
            "description": "Update this task",
            "due_date": (datetime.utcnow() + timedelta(days=2)).isoformat(),
            "assigned_to": MOCK_USER["id"],
            "priority": "low",
        }
        create_response = await client.post("/tasks/", json=task_data, headers=auth_headers())
        task_id = create_response.json()["task_id"]

        # Update the task
        update_data = {"description": "Updated description"}
        response = await client.put(f"/tasks/{task_id}", json=update_data, headers=auth_headers())
        assert response.status_code == 200
        assert response.json()["description"] == "Updated description"

@pytest.mark.asyncio
async def test_delete_task():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create a task to delete
        task_data = {
            "name": "Deletable Task",
            "description": "This task will be deleted",
            "due_date": (datetime.utcnow() + timedelta(days=1)).isoformat(),
            "assigned_to": MOCK_USER["id"],
            "priority": "high",
        }
        create_response = await client.post("/tasks/", json=task_data, headers=auth_headers())
        task_id = create_response.json()["task_id"]

        # Delete the task
        response = await client.delete(f"/tasks/{task_id}", headers=auth_headers())
        assert response.status_code == 200
        assert response.json()["detail"] == "Task deleted successfully"

@pytest.mark.asyncio
async def test_schedule_task():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create a task to schedule
        task_data = {
            "name": "Scheduled Task",
            "description": "This task will be scheduled",
            "due_date": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
            "assigned_to": MOCK_USER["id"],
            "priority": "high",
        }
        create_response = await client.post("/tasks/", json=task_data, headers=auth_headers())
        task_id = create_response.json()["task_id"]

        # Schedule the task
        response = await client.post(f"/tasks/{task_id}/schedule", headers=auth_headers())
        assert response.status_code == 200
        assert response.json()["detail"] == "Reminder scheduled"
