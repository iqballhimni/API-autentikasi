from fastapi import APIRouter, HTTPException, status
from .schemas import UserRegister, UserLogin, ErrorResponse, LoginSuccessResponse
from .auth_service import AuthService

router = APIRouter()

@router.post("/register", 
    response_model=ErrorResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    })
async def register(user: UserRegister):
    return await AuthService.register_user(user)

@router.post("/login",
    response_model=LoginSuccessResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    })
async def login(user: UserLogin):
    return await AuthService.login_user(user)