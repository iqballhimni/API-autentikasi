from fastapi import FastAPI
from app.auth import router as auth_router
from app.firebase import FirebaseInit

db = FirebaseInit.get_firestore()

app = FastAPI(
    title="Authentication API",
    description="API for user authentication"
)

app.include_router(auth_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"status": "healthy", "message": "Authentication API is running"}

@app.get("/_ah/warmup")
async def warmup():
    
    return {"status": "ok"}
