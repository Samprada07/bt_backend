from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic import context
from models import Base  # Make sure to import your models here

config = context.config

# Set up the engine using synchronous connection
def get_url():
    return config.get_main_option("sqlalchemy.url")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode using synchronous engine."""
    engine = create_engine(get_url(), poolclass=None, future=True)
    Session = sessionmaker(bind=engine)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=Base.metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
