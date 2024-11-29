from fastapi import APIRouter, status, File, UploadFile
from typing import Optional
from .schemas import UserRegister, UserLogin, ErrorResponse, LoginSuccessResponse
from .auth_service import AuthService

router = APIRouter()
auth_service = AuthService()

@router.post("/register", 
    response_model=ErrorResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    })
async def register(
    name: str,
    email: str,
    password: str,
    photo: Optional[UploadFile] = File(None)
):
    user = UserRegister(name=name, email=email, password=password)
    return await auth_service.register_user(user, photo)

@router.post("/login",
    response_model=LoginSuccessResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    })

async def login(user: UserLogin):
    return await auth_service.login_user(user)
