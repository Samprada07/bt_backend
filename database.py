from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.schema import MetaData
from sqlalchemy.future import select
from passlib.context import CryptContext
import config
from models import User  # Ensure models.py has the User model

# Define the database engine
engine = create_async_engine(config.DATABASE_URL, echo=True)

# Define session and base model
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()
metadata = MetaData()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dependency to get a database session
async def get_db():
    async with SessionLocal() as session:
        yield session

# Function to create tables asynchronously
async def create_tables():
    """Asynchronously creates all tables in the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Function to create the admin user if it doesn't exist
async def create_admin():
    """Ensure there is only one admin in the database."""
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "admin@gmail.com"))
        admin = result.scalars().first()

        if not admin:
            admin_user = User(
                username="admin",
                email="admin@gmail.com",
                password=pwd_context.hash("admin123"),
                role="admin"
            )
            session.add(admin_user)
            await session.commit()

# Function to initialize the database (create tables and ensure admin user)
async def init_db():
    await create_tables()
    await create_admin()
