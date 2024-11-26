from firebase_admin import auth
from fastapi import HTTPException, status
from .schemas import UserRegister, UserLogin, LoginResult, ErrorResponse, LoginSuccessResponse
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthService:
    @staticmethod
    async def register_user(user: UserRegister) -> ErrorResponse:
        try:
            try:
                existing_user = auth.get_user_by_email(user.email)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorResponse(
                        error=True,
                        message="Email already registered"
                    ).dict()
                )
            except auth.UserNotFoundError:
                pass

            user_record = auth.create_user(
                email=user.email,
                password=user.password,
                display_name=user.name
            )

            return ErrorResponse(
                error=False,
                message="User Created"
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
                ).dict()
            )

    @staticmethod
    async def login_user(user: UserLogin) -> LoginSuccessResponse:
        try:
            user_record = auth.get_user_by_email(user.email)
            
            custom_token = auth.create_custom_token(user_record.uid)
            
            login_result = LoginResult(
                userId=f"user-{user_record.uid[:10]}",
                name=user_record.display_name or "",  # Handle None case
                token=custom_token.decode()
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
                ).dict()
            )
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error=True,
                    message=str(e)
                ).dict()
            )