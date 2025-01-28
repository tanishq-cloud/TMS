from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import sessionmaker
from sqlalchemy import inspect
from dotenv import load_dotenv
import os

load_dotenv()
# PostgreSQL database URL
psg_user = os.getenv('PSG_USER')
psg_password = os.getenv('PSG_PASSWORD')
psg_database = os.getenv('PSG_DATABASE')

# Validate critical environment variables
required_env_vars = ['PSG_USER', 'PSG_PASSWORD', 'PSG_DATABASE']
# missing_vars = [var for var in required_env_vars if not os.getenv(var)]

if missing_vars := [var for var in required_env_vars if not os.getenv(var)]:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}. "
                     "Please set these in your .env file or environment.")
    
DATABASE_URL = f"postgresql+asyncpg://{psg_user}:{psg_password}@localhost:5432/{psg_database}"

# Create async engine for PostgreSQL
engine = create_async_engine(DATABASE_URL, echo=True)

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
