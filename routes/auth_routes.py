from fastapi import APIRouter, Body, Depends, HTTPException
from requests import Session
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from utils.email_utils import send_reset_email
from models import User
from auth import create_reset_token, verify_password, create_access_token, verify_reset_token
from sqlalchemy.future import select
from pydantic import BaseModel
from auth import hash_password
from utils.reponse import success_response
from schemas import ForgotPasswordRequest, ResetPasswordRequest

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
async def login_user(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Fetch user from database
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar()

    if not user or not verify_password(request.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not request.email or not request.password:
        raise HTTPException(status_code=400, detail="Email or password cannot be empty")
    # Generate token with role info
    token = create_access_token({"sub": str(user.id), "role": user.role})


    # Redirect based on role
    if user.role == "admin":
        data = {"name": user.username, "role": "admin", "token": token, "redirect": "/admin_dashboard"}
    else:
        data = {"name": user.username, "role": "Normal user", "token": token, "redirect": "/upload_page"}

    return success_response(data, "Login successful")

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest = Body(...), db: Session = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar()
    
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered")

    token = create_reset_token(user.id)
    reset_url = f"http://localhost:3000/reset-password/{token}"
    await send_reset_email(user.email, reset_url)
    return {"message": "Reset link sent to email"}

@router.post("/reset-password/{token}")
async def reset_password(token: str, request: ResetPasswordRequest = Body(...), db: Session = Depends(get_db)):
    print(token)
    user_id = verify_reset_token(token)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar()
    user.password = hash_password(request.password)
    db.add(user)
    await db.commit()
    return {"message": "Password updated successfully"}

