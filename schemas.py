from pydantic import BaseModel, Field

class UserRegisterSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6, max_length=100)

class UserLoginSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)

class MRIUploadSchema(BaseModel):
    file_path: str = Field(..., min_length=3)
