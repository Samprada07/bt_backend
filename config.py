from pydantic_settings import BaseSettings
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str = "postgresql://postgres:root@localhost:5432/brainTumor"  
    
    # JWT settings
    SECRET_KEY: str = "blehblehhey"  
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File upload settings
    UPLOAD_DIR: str = "uploads"
    TEMP_UPLOAD_DIR: str = "temp_uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: List[str] = ["png", "jpg", "jpeg", "dicom"]
    
    # Model settings
    MRI_VALIDATOR_MODEL_PATH = "brainMri_validator"
    TUMOR_CLASSIFIER_MODEL_PATH = "brain_tumor_model"
    
    # CORS settings
    cors_origins: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False  # This allows case-insensitive field matching

# Create global settings instance
settings = Settings()

# Export settings values that will be imported by other modules
DATABASE_URL = settings.DATABASE_URL
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
UPLOAD_DIR = settings.UPLOAD_DIR
TEMP_UPLOAD_DIR = settings.TEMP_UPLOAD_DIR
MAX_FILE_SIZE = settings.MAX_FILE_SIZE
ALLOWED_EXTENSIONS = settings.ALLOWED_EXTENSIONS
CORS_ORIGINS = settings.cors_origins
