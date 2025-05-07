from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import MRIImage, Prediction, User, ClassificationResults
from auth import get_current_user
import os
from PIL import Image
import numpy as np
import tensorflow as tf


router = APIRouter()

# Upload MRI file, predict, and return prediction + confidence
@router.post("/upload")
async def classify_mri(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload MRI image, validate, classify tumor type, and save results."""
    try:
        # Save the uploaded file temporarily
        contents = await file.read()
        temp_path = os.path.join("temp_uploads", file.filename)
        os.makedirs("temp_uploads", exist_ok=True)
        with open(temp_path, "wb") as f:
            f.write(contents)

        # Save permanent copy in uploads directory
        upload_path = os.path.join("uploads", file.filename)
        os.makedirs("uploads", exist_ok=True)
        with open(upload_path, "wb") as f:
            f.write(contents)

        try:
            # Load models from app.state
            mri_validator_model = request.app.state.brainMri_validator
            tumor_classifier_model = request.app.state.brain_tumor_model

            # Step 1: Validate if image is a brain MRI
            img = Image.open(temp_path).convert("L").resize((224, 224))
            img_array = np.array(img) / 255.0
            validator_input = np.expand_dims(img_array, axis=(0, -1))
            validator_input = tf.convert_to_tensor(validator_input, dtype=tf.float32)

            # Convert to RGB if validator expects 3 channels
            if mri_validator_model.input_shape[-1] == 3:
                validator_input = tf.image.grayscale_to_rgb(validator_input)
                
            validator_input_tensor = tf.convert_to_tensor(validator_input, dtype=tf.float32)
            mri_prob = mri_validator_model.predict(validator_input_tensor)[0][0]
            if mri_prob < 0.7:
                os.remove(temp_path)
                os.remove(upload_path)
                raise HTTPException(status_code=400, detail="This is not a MRI image. Please upload a valid brain MRI scan.")

            # Step 2: Classify tumor
            classifier_input = np.expand_dims(img_array, axis=(0, -1))
            classifier_input = tf.convert_to_tensor(classifier_input, dtype=tf.float32)
            prediction = tumor_classifier_model.predict(classifier_input)[0]
            predicted_class_index = int(np.argmax(prediction))
            confidence_score = float(np.max(prediction)) * 100

            # Class label mapping
            class_mappings = {0: "Glioma", 1: "Meningioma", 2: "No Tumor", 3: "Pituitary"}
            predicted_label = class_mappings.get(predicted_class_index, "Unknown")

            # Save MRI image record
            mri_image = MRIImage(
                file_path=upload_path,
                user_id=current_user.id
            )
            db.add(mri_image)
            await db.commit()
            await db.refresh(mri_image)

            # Save classification result
            result = ClassificationResults(
                user_id=current_user.id,
                mri_image_id=mri_image.id,
                result=f"{predicted_label} (Confidence: {confidence_score:.2f}%)",
                confidence=confidence_score,
                prediction=Prediction.NEGATIVE if predicted_label == "No Tumor" else Prediction.POSITIVE
            )
            db.add(result)
            await db.commit()
            await db.refresh(result)

            # Cleanup
            os.remove(temp_path)

            return {
                "prediction": predicted_label,
                "confidence": f"{confidence_score:.2f}",
                "mri_image_id": mri_image.id,
                "classification_id": result.id
            }

        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(upload_path):
                os.remove(upload_path)
            raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

