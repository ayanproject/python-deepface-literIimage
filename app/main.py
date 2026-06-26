from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import bcrypt
import os
from app import config
from app.utils import save_bytes_to_tempfile
from app.verifier import verify_faces_by_path

app = FastAPI(title="Face Verification Service")

# ---- CORS FIX ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500", "https://votonn.netlify.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def fetch_user_from_postgres(voter_id: str):
    conn = None
    try:
        # Using psycopg2 instead of pymysql
        conn = psycopg2.connect(
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            dbname=config.DB_DATABASE,  # Changed from 'database' to 'dbname'
            port=config.DB_PORT
        )
        conn.autocommit = True

        # RealDictCursor makes rows act like dictionaries just like DictCursor did
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Removed backticks since Postgres uses double quotes or no quotes for tables
            sql = f"SELECT face_image, encrypted_voter_id, encrypted_secret_pin, email, name FROM {config.DB_TABLE};"
            cur.execute(sql)
            rows = cur.fetchall()

            for row in rows:
                # Handle bytes vs strings safely in PostgreSQL
                stored_voter_id = row["encrypted_voter_id"]
                if isinstance(stored_voter_id, str):
                    stored_voter_id = stored_voter_id.encode()
                elif isinstance(stored_voter_id, memoryview):
                    stored_voter_id = stored_voter_id.tobytes()

                if bcrypt.checkpw(voter_id.encode(), stored_voter_id):
                    return row 

            return None 

    finally:
        if conn:
            conn.close()


@app.post("/verify")
async def verify_face(
    voter_id: str = Form(...),
    secret_pin: str = Form(...),
    probe_image: UploadFile = File(...)
):
    # Call the updated postgres function
    user = fetch_user_from_postgres(voter_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Safely extract bytes from postgres results
    stored_voter_id = user["encrypted_voter_id"]
    stored_pin = user["encrypted_secret_pin"]
    
    if isinstance(stored_voter_id, str): stored_voter_id = stored_voter_id.encode()
    if isinstance(stored_pin, str): stored_pin = stored_pin.encode()

    # Check credentials
    if not bcrypt.checkpw(voter_id.encode(), stored_voter_id):
        return {"verified": False, "reason": "Wrong Voter ID"}

    if not bcrypt.checkpw(secret_pin.encode(), stored_pin):
        return {"verified": False, "reason": "Wrong Secret PIN"}

    # Handle binary data format from postgres for images safely
    face_image_bytes = user["face_image"]
    if isinstance(face_image_bytes, memoryview):
        face_image_bytes = face_image_bytes.tobytes()

    # Save stored + probe images temporarily
    stored_path = save_bytes_to_tempfile(face_image_bytes)
    probe_path = save_bytes_to_tempfile(await probe_image.read())

    # Call the lightweight verifier
    result = verify_faces_by_path(probe_path, stored_path)

    os.remove(stored_path)
    os.remove(probe_path)

    return {
        "verified": bool(result.get("verified", False)),
        "distance": result.get("distance"),
        "reason": result.get("reason", ""),
        "email": user.get("email"),
        "name": user.get("name")
    }