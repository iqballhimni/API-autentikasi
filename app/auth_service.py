from firebase_admin import auth
from fastapi import HTTPException, status
from .schemas import UserRegister, UserLogin, LoginResult, ErrorResponse, LoginSuccessResponse
import logging

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AuthService:
    @staticmethod
    async def register_user(user: UserRegister) -> ErrorResponse:
        try:
            
            try:
                auth.get_user_by_email(user.email)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": True,
                        "message": "Email already registered"
                    }
                )
            except auth.UserNotFoundError:
                pass

            user_record = auth.create_user(
                email=user.email,
                password=user.password,
                display_name=user.name
            )

            logger.info(f"User registered successfully: {user.email}")
            return ErrorResponse(
                error=False,
                message="User Created"
            )

        except HTTPException as http_error:
            logger.error(f"Registration HTTP error: {http_error.detail}")
            raise
        except Exception as e:
            logger.error(f"Unexpected registration error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": True,
                    "message": "Registration failed"
                }
            )

    @staticmethod
    async def login_user(user: UserLogin) -> LoginSuccessResponse:
        try:
            user_record = auth.get_user_by_email(user.email)
            
            custom_token = auth.create_custom_token(user_record.uid)
            
            token = custom_token.decode('utf-8') if isinstance(custom_token, bytes) else custom_token

            login_result = LoginResult(
                userId=f"user-{user_record.uid[:10]}",
                name=user_record.display_name or "",
                token=token
            )

            logger.info(f"User logged in successfully: {user.email}")
            return LoginSuccessResponse(
                error=False,
                message="success",
                loginResult=login_result
            )

        except auth.UserNotFoundError:
            logger.warning(f"Login attempt for non-existent user: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": True,
                    "message": "User not found"
                }
            )
        except Exception as e:
            logger.error(f"Unexpected login error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": True,
                    "message": "Login failed"
                }
            )
