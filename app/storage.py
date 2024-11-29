from firebase_admin import storage
import os
from fastapi import UploadFile
from typing import Optional
import uuid
from .firebase import FirebaseInit

class StorageService:
    def __init__(self):
        self.bucket = FirebaseInit.get_storage()
    
    async def upload_profile_photo(self, file: UploadFile) -> Optional[str]:
        
        content = await file.read()
        if len(content) > 1_048_576:
            raise ValueError("the photo size must be less than 1MB")
            
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ['.jpg', '.png']:
            raise ValueError("Only .jpg and .png files are allowed")
            
        unique_filename = f"profile_photos/{str(uuid.uuid4())}{file_ext}"
        
        blob = self.bucket.blob(unique_filename)
        blob.upload_from_string(content, content_type=file.content_type)
        
        blob.make_public()
        
        return blob.public_url
