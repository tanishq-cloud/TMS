from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import sessionmaker
from sqlalchemy import inspect

# PostgreSQL database URL
DATABASE_URL = "postgresql+asyncpg://cooluser:cool@localhost:5432/tasks"

# Create async engine for PostgreSQL
engine = create_async_engine(DATABASE_URL, echo=True)

# Async session maker
async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
)

@as_declarative()
class Base:
    id: int
    __name__: str

    # Automatically generate table name
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

# Initialize the database schema
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Dependency to get async session
async def get_db():
    async with async_session() as db:
        try:
            yield db
        finally:
            await db.close()
            
async def table_exists(table_name: str, db: AsyncSession) -> bool:
    inspector = inspect(db.bind)
    return table_name in inspector.get_table_names()
