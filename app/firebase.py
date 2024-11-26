import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import os
from pathlib import Path

# Memuat file .env
load_dotenv()

def initialize_firebase():
    try:
        # Mengambil path dari file .env jika ada (jika tidak, gunakan default path)
        service_key_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        
        if not service_key_path:
            # Jika tidak ada path di .env, coba menggunakan path default
            root_dir = Path(__file__).resolve().parent
            service_key_path = root_dir / "service" / "serviceKey.json"

        service_path = Path(service_key_path)
        
        # Periksa apakah file serviceKey.json ada
        if not service_path.exists():
            raise FileNotFoundError(f"Service account file not found at: {service_path}")

        # Inisialisasi Firebase jika belum ada aplikasi yang aktif
        if not firebase_admin._apps:
            cred = credentials.Certificate(str(service_path))
            firebase_admin.initialize_app(cred)

        return firestore.client()
    
    except Exception as e:
        print(f"Firebase initialization error: {str(e)}")  # Menambahkan logging
        raise Exception(f"Failed to initialize Firebase: {str(e)}")


_db = None

def get_firestore_client():
    """Returns the Firestore client instance"""
    global _db
    if _db is None:
        try:
            _db = initialize_firebase()
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            raise
    return _db