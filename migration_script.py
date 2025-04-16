import os
import subprocess
from alembic.config import Config
from alembic import command
from sqlalchemy.exc import OperationalError

# Define the path to your alembic.ini configuration file
ALEMBIC_CONFIG = os.path.join(os.path.dirname(__file__), 'alembic.ini')

def generate_migration(message):
    """Generate a new migration script based on changes in models."""
    # Load the Alembic configuration
    alembic_cfg = Config(ALEMBIC_CONFIG)
    
    try:
        print(f"Generating migration script with message: {message}")
        subprocess.run(["alembic", "revision", "--autogenerate", "-m", message], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error generating migration: {e}")
        return False
    return True

def apply_migration():
    """Apply the most recent migration."""
    alembic_cfg = Config(ALEMBIC_CONFIG)
    
    try:
        print("Applying the latest migration...")
        command.upgrade(alembic_cfg, "head")
        print("Migration applied successfully.")
    except OperationalError as e:
        print(f"Error applying migration: {e}")
        print("This could be due to a missing migration file. Please check the migration history.")
        return False
    except Exception as e:
        print(f"Error applying migration: {e}")
        return False
    return True

def create_and_apply_migration(message):
    """Generate and apply migration script."""
    if generate_migration(message):
        return apply_migration()
    return False

if __name__ == "__main__":
    # Example: Create and apply a migration with a custom message
    message = "Add new column to ClassificationResults"
    
    # Handle missing or deleted migration files
    try:
        if create_and_apply_migration(message):
            print("Migration created and applied successfully.")
        else:
            print("An error occurred during migration process.")
    except Exception as e:
        print(f"An error occurred: {e}")
