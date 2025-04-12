from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.schema import MetaData
from sqlalchemy.future import select
from passlib.context import CryptContext
import asyncpg
from config import settings
from models import User, Base  # Import Base from models
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the database engine with the correct URL format
engine = create_async_engine(
    f"postgresql+asyncpg://postgres:root@localhost:5432/brainTumor",
    echo=True
)

# Define session and base model
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
metadata = MetaData()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Function to create database if it doesn't exist
async def create_database():
    """Create the database if it doesn't exist."""
    try:
        conn = await asyncpg.connect(
            user='postgres',
            password='root',
            database='postgres',
            host='localhost'
        )
        await conn.execute('CREATE DATABASE "brainTumor"')
        logger.info("Database 'brainTumor' created successfully")
        await conn.close()
    except asyncpg.exceptions.DuplicateDatabaseError:
        logger.info("Database 'brainTumor' already exists, skipping creation.")
    except Exception as e:
        logger.error(f"Error creating database: {str(e)}")
        raise

# Dependency to get a database session
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e

# Function to create tables asynchronously
async def create_tables():
    """Asynchronously creates all tables in the database."""
    try:
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise

# Function to create the admin user if it doesn't exist
async def create_admin():
    """Ensure there is only one admin in the database."""
    async with SessionLocal() as session:
        async with session.begin():  # Automatically rollback on failure
            result = await session.execute(
                select(User).where(User.email == "admin@gmail.com")
            )
            admin = result.scalars().first()

            if not admin:
                admin_user = User(
                    username="admin",
                    email="admin@gmail.com",
                    password=pwd_context.hash("admin123"),
                    role="admin"
                )
                session.add(admin_user)
                logger.info("Admin user created successfully")
            else:
                logger.info("Admin user already exists")


# Function to initialize the database (create tables and ensure admin user)
async def init_db():
    """Initialize database with tables and admin user."""
    try:
        # First ensure database exists
        await create_database()
        # Then create tables
        await create_tables()
        # Finally create admin user
        await create_admin()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
