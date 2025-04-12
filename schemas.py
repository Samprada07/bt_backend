from pydantic import BaseModel, Field, EmailStr

class UserRegisterSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6, max_length=100)

class UserLoginSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)

class MRIUploadSchema(BaseModel):
    file_path: str = Field(..., min_length=3)

class ClassificationResultSchema(BaseModel):
    user_id: int
    mri_image_id: int
    result: str

    class Config:
        from_attributes = True

class ClassificationResultResponse(BaseModel):
    id: int
    user_id: int
    mri_image_id: int
    result: str

    class Config:
        from_attributes = True

class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    
class ResetPasswordRequest(BaseModel):
    password: str