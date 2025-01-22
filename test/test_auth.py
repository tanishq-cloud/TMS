import pytest
from httpx import AsyncClient
from app.main import app  # Assuming the FastAPI app is defined in `main.py`
from app.database import get_db
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Base

# Set up a test database URL (SQLite in-memory database for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Configure the test database session
engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Dependency override for the database
async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

# Set up the database
@pytest.fixture(autouse=True, scope="module")
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.mark.asyncio
async def test_register_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register a new user
        user_data = {"username": "testuser", "password": "password123"}
        response = await client.post("/register", json=user_data)
        assert response.status_code == 200
        assert response.json()["username"] == "testuser"

        # Try to register the same user again
        response = await client.post("/register", json=user_data)
        assert response.status_code == 400
        assert response.json()["detail"] == "Username already taken"

@pytest.mark.asyncio
async def test_login_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Register a user for login testing
        user_data = {"username": "testuser", "password": "password123"}
        await client.post("/register", json=user_data)

        # Successful login
        login_data = {"username": "testuser", "password": "password123"}
        response = await client.post("/login", data=login_data)
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

        # Login with incorrect password
        login_data = {"username": "testuser", "password": "wrongpassword"}
        response = await client.post("/login", data=login_data)
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"

        # Login with a non-existent user
        login_data = {"username": "nonexistent", "password": "password123"}
        response = await client.post("/login", data=login_data)
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid credentials"
