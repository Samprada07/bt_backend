from fastapi import FastAPI
from routes import user_routes, auth_routes, mri_routes, classification_routes
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from database import init_db
from config import settings
import os
from fastapi.staticfiles import StaticFiles

# Lazy load tensorflow model
import tensorflow as tf

app = FastAPI()

# Define allowed origins
origins = settings.cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(user_routes.router, prefix="/users", tags=["Users"])
app.include_router(mri_routes.router, prefix="/mri", tags=["MRI"])
app.include_router(auth_routes.router, prefix="/auth", tags=["Auth"])
app.include_router(classification_routes.router, prefix="/classification", tags=["Classification"])

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")

def load_models():
    """Loads and stores both MRI validator and tumor classifier models."""
    if not hasattr(app.state, "mri_validator_model"):
        validator_path = Path(settings.MRI_VALIDATOR_MODEL_PATH).resolve()
        if validator_path.with_suffix(".keras").exists():
            validator_path = validator_path.with_suffix(".keras")
        elif validator_path.with_suffix(".h5").exists():
            validator_path = validator_path.with_suffix(".h5")
        else:
            raise ValueError(f"Validator model not found: {validator_path}")
        app.state.mri_validator_model = tf.keras.models.load_model(str(validator_path))
        print("MRI validator model loaded.")

    if not hasattr(app.state, "tumor_classifier_model"):
        classifier_path = Path(settings.TUMOR_CLASSIFIER_MODEL_PATH).resolve()
        if classifier_path.with_suffix(".keras").exists():
            classifier_path = classifier_path.with_suffix(".keras")
        elif classifier_path.with_suffix(".h5").exists():
            classifier_path = classifier_path.with_suffix(".h5")
        else:
            raise ValueError(f"Tumor classifier model not found: {classifier_path}")
        app.state.tumor_classifier_model = tf.keras.models.load_model(str(classifier_path))
        print("Tumor classifier model loaded.")


@app.on_event("startup")
async def startup():
    # Initialize database (this will create database, tables, and admin user)
    await init_db()
    load_models() 
    print("Database initialized successfully.")
    

@app.get("/predict")
async def predict():
    load_models()  # Load model when called
    return {"message": "Model is ready for predictions."}

# Access model anywhere via app.state.model
