import requests
import os
import logging
import uuid
from typing import Optional
from fastapi import HTTPException, status, UploadFile
from firebase_admin import auth
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from .schemas import (
    UserRegister,
    UserLogin,
    LoginResult,
    LoginSuccessResponse,
    LoginFailureResponse,
    ProfileResponse,
    ErrorResponse,
)
from .storage import StorageService

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthService:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AuthService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not AuthService._initialized:
            self.storage_service = StorageService()
            self.api_key = os.getenv('FIREBASE_API_KEY')
            if not self.api_key:
                raise ValueError("FIREBASE_API_KEY not set in environment variables")
            AuthService._initialized = True

    async def extract_token(self, authorization: Optional[str]) -> str:
        logger.info("Extracting token from authorization header")
        if not authorization or not authorization.startswith('Bearer '):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse(
                    error=True,
                    message="Invalid authorization header format"
                ).model_dump()
            )
        return authorization.split('Bearer ')[1].strip()

    async def verify_token(self, token: str) -> Optional[str]:
        try:
            logger.info("Verifying token")
            decoded_token = auth.verify_id_token(token)
            logger.info("Token verified successfully")
            return decoded_token['uid']
        except auth.InvalidIdTokenError:
            logger.error("Invalid token error")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse(
                    error=True,
                    message="Invalid token"
                ).model_dump()
            )
        except auth.ExpiredIdTokenError:
            logger.error("Token expired error")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse(
                    error=True,
                    message="Token has expired"
                ).model_dump()
            )
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error=True,
                    message="Error verifying token"
                ).model_dump()
            )

    async def get_firebase_token(self, email: str, password: str) -> str:
        try:
            logger.info(f"Getting Firebase token for email: {email}")
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}"
            response = requests.post(url, json={
                "email": email,
                "password": password,
                "returnSecureToken": True
            })
            
            if response.status_code != 200:
                error_message = response.json().get('error', {}).get('message', 'Invalid credentials')
                logger.error(f"Firebase token error: {error_message}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=LoginFailureResponse(
                        message=error_message
                    ).model_dump()
                )
            
            logger.info("Firebase token obtained successfully")
            return response.json()['idToken']
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Firebase token error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error=True,
                    message="Error getting Firebase token"
                ).model_dump()
            )

    async def login_user(self, user: UserLogin) -> LoginSuccessResponse:
        try:
            logger.info(f"Attempting login for email: {user.email}")
            
            id_token = await self.get_firebase_token(user.email, user.password)
            
            user_record = auth.get_user_by_email(user.email)
            logger.info(f"User found: {user_record.uid}")

            return LoginSuccessResponse(
                error=False,
                message="Login successful",
                loginResult=LoginResult(
                    userId=f"user-{user_record.uid[:10]}",
                    name=user_record.display_name or "",
                    token=id_token,
                    photo_url=user_record.photo_url,
                    isSignedIn=True
                )
            )
        except auth.UserNotFoundError:
            logger.error(f"User not found: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=LoginFailureResponse(
                    message="Invalid email or password"
                ).model_dump()
            )
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error=True,
                    message="Authentication failed"
                ).model_dump()
            )

    async def get_user_profile(self, token: str) -> ProfileResponse:
        try:
            logger.info("Getting user profile")
            user_id = await self.verify_token(token)
            user_record = auth.get_user(user_id)
            logger.info(f"Retrieved profile for user: {user_id}")

            return ProfileResponse(
                error=False,
                message="Profile retrieved successfully",
                detail={
                    "name": user_record.display_name or "",
                    "photo_url": user_record.photo_url or ""
                }
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Profile retrieval error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error=True,
                    message="Error retrieving user profile"
                ).model_dump()
            )

    async def register_user(self, user: UserRegister, photo: Optional[UploadFile] = None) -> LoginSuccessResponse:
        try:
            logger.info(f"Starting registration for email: {user.email}")
            
            # Check if user already exists
            try:
                existing_user = auth.get_user_by_email(user.email)
                logger.warning(f"Email already registered: {user.email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ErrorResponse(
                        error=True,
                        message="Email already registered"
                    ).model_dump()
                )
            except auth.UserNotFoundError:
                pass  # User doesn't exist, continue registration

            # Upload photo if provided
            photo_url = None
            if photo:
                try:
                    logger.info("Uploading profile photo")
                    file_extension = os.path.splitext(photo.filename)[1]
                    
                    photo_path = f"profile_photos/{str(uuid.uuid4())}{file_extension}"
                    photo_url = await self.storage_service.upload_file(photo, photo_path)
                    logger.info(f"Photo uploaded successfully: {photo_url}")
                    
                except Exception as e:
                    logger.error(f"Photo upload error: {str(e)}")
            
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=ErrorResponse(
                            error=True,
                            message=f"Error uploading photo: {str(e)}"
                        ).model_dump()
                    )

            user_params = {
                "email": user.email,
                "password": user.password,
                "display_name": user.name
            }
            
            if photo_url:
                user_params["photo_url"] = photo_url

            logger.info("Creating user in Firebase Authentication")
            user_record = auth.create_user(**user_params)
            logger.info(f"User created successfully with ID: {user_record.uid}")

            # Get Firebase ID token for immediate sign-in
            token = await self.get_firebase_token(user.email, user.password)

            return LoginSuccessResponse(
                error=False,
                message="Registration successful"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse(
                    error=True,
                    message=f"Registration failed: {str(e)}"
                ).model_dump()
            )
