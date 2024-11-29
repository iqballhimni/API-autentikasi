from firebase_admin import auth
from fastapi import HTTPException, status, UploadFile
from .schemas import UserRegister, UserLogin, LoginResult, ErrorResponse, LoginSuccessResponse
from .storage import StorageService
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self):
        self.storage_service = StorageService()

    @staticmethod
    def _create_user_without_photo(user: UserRegister):
        return auth.create_user(
            email=user.email,
            password=user.password,
            display_name=user.name
        )

    async def register_user(self, user: UserRegister, photo: Optional[UploadFile] = None) -> ErrorResponse:
        try:
            try:
                existing_user = auth.get_user_by_email(user.email)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorResponse(
                        error=True,
                        message="Email already registered"
                    ).model_dump()
                )
            except auth.UserNotFoundError:
                pass

            user_record = self._create_user_without_photo(user)
            
            if photo:
                try:
                    photo_url = await self.storage_service.upload_profile_photo(photo)
                    # Update user profile with photo URL
                    auth.update_user(
                        user_record.uid,
                        photo_url=photo_url
                    )
                except ValueError as e:
                    
                    logger.error(f"Photo upload failed: {str(e)}")
                    return ErrorResponse(
                        error=False,
                        message=f"User created but photo upload failed: {str(e)}"
                    )

            return ErrorResponse(
                error=False,
                message="User Created Successfully"
            )

        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error=True,
                    message=str(e)
                ).model_dump()
            )

    @staticmethod
    async def login_user(user: UserLogin) -> LoginSuccessResponse:
        try:
            user_record = auth.get_user_by_email(user.email)
            
            custom_token = auth.create_custom_token(user_record.uid)
            
            login_result = LoginResult(
                userId=f"user-{user_record.uid[:10]}",
                name=user_record.display_name or "",
                token=custom_token.decode(),
                photo_url=user_record.photo_url
            )

            return LoginSuccessResponse(
                error=False,
                message="success",
                loginResult=login_result
            )

        except auth.UserNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error=True,
                    message="User not found"
                ).model_dump()
            )
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error=True,
                    message=str(e)
                ).model_dump()
            )
