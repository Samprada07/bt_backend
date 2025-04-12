from sqlalchemy import Column, Enum, Float, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum
# Create Base class for models
Base = declarative_base()

class Prediction(enum.Enum):
    """Enum representing possible predictions."""
    POSITIVE = "Positive"
    NEGATIVE = "Negative"

class User(Base):
    """User model representing application users."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="Normal user")

    mri_images = relationship("MRIImage", cascade="all, delete-orphan", back_populates="user")
    classification_results = relationship("ClassificationResults", cascade="all, delete-orphan", back_populates="user")

class MRIImage(Base):
    """Model representing MRI image uploads."""
    __tablename__ = "mri_images"

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="mri_images")
    classification_results = relationship("ClassificationResults", back_populates="mri_image")
  
class ClassificationResults(Base):  
    """Model representing brain tumor classification results."""
    __tablename__ = "classification_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    mri_image_id = Column(Integer, ForeignKey("mri_images.id"))
    result = Column(String)
    prediction = Column(Enum(Prediction), default=Prediction.NEGATIVE)
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="classification_results")
    mri_image = relationship("MRIImage", back_populates="classification_results")
    

