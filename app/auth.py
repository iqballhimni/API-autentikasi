from fastapi import APIRouter, status, File, Form, UploadFile, Header, HTTPException, Depends
from typing import Optional
from .schemas import UserRegister, UserLogin, ErrorResponse, LoginSuccessResponse, ProfileResponse
from .auth_service import AuthService

router = APIRouter()

@router.post("/register",
    response_model=LoginSuccessResponse,
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
    auth_service = AuthService()
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
    auth_service = AuthService()
    return await auth_service.login_user(user)

@router.get("/userProfile",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"model": ProfileResponse},
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def get_profile(authorization: Optional[str] = Header(None)):
    auth_service = AuthService()
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error=True,
                message="Authorization header is missing"
            ).model_dump()
        )
    
    token = await auth_service.extract_token(authorization)
    user_profile = await auth_service.get_user_profile(token)
    
    return user_profile
