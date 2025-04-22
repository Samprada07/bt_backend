from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import Delete
from database import get_db
from models import ClassificationResults, MRIImage, User
from schemas import UserRegisterSchema
from auth import get_current_user, hash_password, role_guard
from utils.reponse import success_response  # Assuming this function hashes passwords

router = APIRouter()

@router.post("/register")
async def register_user(request: UserRegisterSchema, db: AsyncSession = Depends(get_db)):
    # Prevent new users from registering as admin
    if request.username == "admin@gmail.com":
        raise HTTPException(status_code=400, detail="This email is reserved for the admin.")

    # Check if the user already exists
    result = await db.execute(select(User).where(User.username == request.username))
    existing_user = result.scalar()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    result2 = await db.execute(select(User).where(User.email == request.email))
    existing_email = result2.scalar()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")

    # Register as a normal user
    new_user = User(username=request.username, email=request.email, password=hash_password(request.password), role="Normal user")
    db.add(new_user)
    await db.commit()
    return success_response(new_user, "User registered successfully")

@router.get("/all", dependencies=[Depends(role_guard(["admin"]))])
async def get_all_users(db: AsyncSession = Depends(get_db),  current_user: User = Depends(get_current_user)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    
    # Filter out the current user from the list
    users = [user for user in users if user.id != current_user.id]
    return success_response(users, "Users fetched successfully")

@router.get("/prediction-history")
async def get_prediction_history(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        query = (
            select(ClassificationResults, MRIImage, User)
            .join(MRIImage, ClassificationResults.mri_image_id == MRIImage.id)
            .join(User, ClassificationResults.user_id == User.id)
            .where(User.id == current_user.id)
            .order_by(ClassificationResults.id.desc())
        )
        # Execute the query correctly
        result = await db.execute(query)
        predictions = result.all()
        
        results = []
        # Correct tuple unpacking with all three entities
        for classification, mri_image, user in predictions:
            results.append(
                {
                    "result": classification.result,
                    "file_path": mri_image.file_path,
                    "created_at": classification.created_at.isoformat()
                    if hasattr(classification, "created_at")
                    else None,
                }
            )
        return success_response(results, "Prediction history for current user fetched successfully")
    except Exception as e:
        print(f"Error in prediction history: {str(e)}")  # Add debugging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch history of current user: {str(e)}",
        )
    
@router.delete("/{user_id}", dependencies=[Depends(role_guard(["admin"]))])
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    try:
        # Start transaction
        async with db.begin():
            user = await db.execute(select(User).where(User.id == user_id))
            user = user.scalar()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            await db.delete(user)
            await db.commit()   
            
            return success_response({"user_id": user_id}, "User deleted successfully")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")
