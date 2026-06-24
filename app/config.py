import os
from dotenv import load_dotenv

# Load .env (optional for local)
load_dotenv()

# PostgreSQL / Supabase credentials
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 6543)) # Default shifted to 6543 for Supabase connection pooling
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DATABASE = os.getenv("DB_NAME")

# Table name (static)
DB_TABLE = "user_face_entity"

# Temporary file settings
TMP_FILE_SUFFIX = ".jpg"

# Frontend URL (for CORS)
FRONTEND_URL = os.getenv("FRONTEND_URL")