from pydantic import BaseModel

class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class LoginResult(BaseModel):
    userId: str
    name: str
    token: str

class ErrorResponse(BaseModel):
    error: bool
    message: str

class LoginSuccessResponse(BaseModel):
    error: bool
    message: str
    loginResult: LoginResult
