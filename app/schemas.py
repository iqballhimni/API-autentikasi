from pydantic import BaseModel
from typing import Optional

class UserRegister(BaseModel):
    name: str 
    email: str 
    password: str
    photo_url: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class LoginResult(BaseModel):
    userId: str
    name: str
    token: str
    photo_url: Optional[str] = None

class ErrorResponse(BaseModel):
    error: bool
    message: str

class LoginSuccessResponse(BaseModel):
    error: bool
    message: str
    loginResult: LoginResult
