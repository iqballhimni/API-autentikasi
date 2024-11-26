from fastapi import FastAPI
from app.firebase import get_firestore_client
from app.auth import router as auth_router

db = get_firestore_client()

app = FastAPI(
    title="Authentication API",
    description="API for user authentication"
)

app.include_router(auth_router)