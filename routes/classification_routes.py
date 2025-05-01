import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from models import ClassificationResults, Prediction, User, MRIImage
from schemas import ClassificationResultSchema, ClassificationResultResponse
from auth import get_current_user
from typing import List
from datetime import datetime

from utils.reponse import success_response

router = APIRouter()


@router.post("/save", response_model=ClassificationResultResponse)
async def save_classification_result(
    result: ClassificationResultSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save a new classification result."""
    try:
        # Verify that the MRI image exists and belongs to the user
        mri_query = select(MRIImage).where(
            MRIImage.id == result.mri_image_id, MRIImage.user_id == current_user.id
        )
        mri_result = await db.execute(mri_query)
        mri_image = mri_result.scalar_one_or_none()

        if not mri_image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MRI image not found or does not belong to the current user",
            )

        # Create new classification result
        classification_result = ClassificationResults(
            user_id=current_user.id,
            mri_image_id=result.mri_image_id,
            result=result.result,
        )

        db.add(classification_result)
        await db.commit()
        await db.refresh(classification_result)

        return classification_result
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save classification result: {str(e)}",
        )

@router.delete("/results/{classificationId}")
async def delete_result(classificationId: int, db: AsyncSession = Depends(get_db)):
    try:
        classification = await db.execute(select(ClassificationResults).where(ClassificationResults.id == classificationId))
        classification = classification.scalar()
        if not classification:
            raise HTTPException(status_code=404, detail="Classification result not found")
        await db.delete(classification)
        await db.commit()
        return success_response({"classificationId": classificationId}, "Classification result deleted successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete classification result: {str(e)}")    

@router.get("/user/{user_id}", response_model=List[ClassificationResultResponse])
async def get_user_results(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all classification results for a specific user."""
    # Only admin or the user themselves can view their results
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these results",
        )

    query = select(ClassificationResults).where(
        ClassificationResults.user_id == user_id
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/image/{mri_image_id}", response_model=ClassificationResultResponse)
async def get_image_result(
    mri_image_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the classification result for a specific MRI image."""
    # First check if the MRI image belongs to the current user
    mri_query = select(MRIImage).where(MRIImage.id == mri_image_id)
    mri_result = await db.execute(mri_query)
    mri_image = mri_result.scalar_one_or_none()

    if not mri_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="MRI image not found"
        )

    if current_user.role != "admin" and mri_image.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this result",
        )

    query = select(ClassificationResults).where(
        ClassificationResults.mri_image_id == mri_image_id
    )
    result = await db.execute(query)
    classification = result.scalar_one_or_none()

    if not classification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classification result not found for this image",
        )

    return classification


@router.get("/history")
async def get_prediction_history(db: AsyncSession = Depends(get_db)):
    """Get prediction history for the logged-in user."""
    try:
        # Query to get classification results with MRI image details
        query = (
            select(ClassificationResults, MRIImage, User)
            .join(MRIImage, ClassificationResults.mri_image_id == MRIImage.id)
            .join(User, ClassificationResults.user_id == User.id)
            .order_by(ClassificationResults.id.desc())
        )

        result = await db.execute(query)
        history = result.all()

        # Format the response
        formatted_history = []
        for classification, mri_image, user in history:
            formatted_history.append(
                {
                    "id": classification.id,
                    "user_id": user.id,
                    "username": user.username,
                    "mri_image_id": classification.mri_image_id,
                    "result": classification.result,
                    "file_path": mri_image.file_path,
                    "created_at": classification.created_at.isoformat()
                    if hasattr(classification, "created_at")
                    else None,
                }
            )

        return success_response(
            formatted_history, "Prediction history fetched successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch prediction history: {str(e)}",
        )


@router.get("/analytics")
async def get_analytics(db: AsyncSession = Depends(get_db)):
    """Get analytics for the logged-in user."""
    try:
        userCount = select(func.count()).select_from(User)
        total_users = await db.execute(userCount)
        total_users = total_users.scalar_one()

        predictionCount = select(func.count()).select_from(ClassificationResults)
        total_predictions = await db.execute(predictionCount)
        total_predictions = total_predictions.scalar_one()

        positive_predictions = (
            select(func.count())
            .select_from(ClassificationResults)
            .where(ClassificationResults.prediction == Prediction.POSITIVE)
        )
        positive_predictions = await db.execute(positive_predictions)
        positive_predictions = positive_predictions.scalar_one()

        negative_predictions = (
            select(func.count())
            .select_from(ClassificationResults)
            .where(ClassificationResults.prediction == Prediction.NEGATIVE)
        )
        negative_predictions = await db.execute(negative_predictions)
        negative_predictions = negative_predictions.scalar_one()

        average_confidence = select(
            func.avg(ClassificationResults.confidence)
        ).select_from(ClassificationResults)
        average_confidence = await db.execute(average_confidence)
        average_confidence = average_confidence.scalar_one()

        result = select(ClassificationResults.result)
        result = await db.execute(result)
        results = result.scalars().all()

        def extract_tumor_type(result_str):
            if result_str:
                match = re.match(
                    r"^(Glioma|Meningioma|Pituitary|No Tumor)",
                    result_str,
                    re.IGNORECASE,
                )
            if match:
                return match.group(1).lower()  # Return tumor type in lowercase
            return "unknown"

        # Initialize distribution dictionary
        prediction_distribution = {
            "glioma": 0,
            "meningioma": 0,
            "pituitary": 0,
            "no_tumor": 0,
        }
        # Count occurrences of each tumor type
        for result_str in results:
            tumor_type = extract_tumor_type(result_str)
            if tumor_type in prediction_distribution:
                prediction_distribution[tumor_type] += 1
        # Fetch user activity data (uploads and last upload)
        user_activity_query = select(
            ClassificationResults.user_id,
            func.count(ClassificationResults.user_id).label("uploads"),
            func.max(ClassificationResults.created_at).label(
                "last_upload"
            ),  # Assuming timestamp exists
        ).group_by(ClassificationResults.user_id)

        user_activity_result = await db.execute(user_activity_query)
        user_activity = user_activity_result.all()
        # Format user activity data
        user_activity_list = []
        for user_id, uploads, last_upload in user_activity:
            user_activity_list.append(
                {
                    "user_id": user_id,
                    "uploads": uploads,
                    "last_upload": last_upload.strftime("%Y-%m-%d %H:%M:%S")
                    if last_upload
                    else "N/A",
                }
            )
            # Return the success response with all analytics data
        return success_response(
            {
                "total_users": total_users,
                "total_predictions": total_predictions,
                "positive_predictions": positive_predictions,
                "negative_predictions": negative_predictions,
                "average_confidence": average_confidence,
                "prediction_distribution": prediction_distribution,
                "user_activity": user_activity_list,
            },
            "Analytics fetched successfully",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch prediction history: {str(e)}",
        )
