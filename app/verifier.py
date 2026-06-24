import face_recognition

def verify_faces_by_path(probe_path: str, stored_path: str):
    """
    Loads images using face_recognition, generates facial encodings,
    and returns a verification dictionary matching the original format.
    """
    try:
        # Load the images
        img_probe = face_recognition.load_image_file(probe_path)
        img_stored = face_recognition.load_image_file(stored_path)

        # Get face encodings (feature vectors)
        probe_encodings = face_recognition.face_encodings(img_probe)
        stored_encodings = face_recognition.face_encodings(img_stored)

        # Check if faces were actually detected in both images
        if not probe_encodings or not stored_encodings:
            return {"verified": False, "distance": 1.0, "reason": "Face not detected in one or both images"}

        # Compare faces (Tolerance 0.55 is a solid strict baseline for security)
        matches = face_recognition.compare_faces([stored_encodings[0]], probe_encodings[0], tolerance=0.55)
        distance = face_recognition.face_distance([stored_encodings[0]], probe_encodings[0])[0]

        return {
            "verified": bool(matches[0]),
            "distance": float(distance)
        }
    except Exception as e:
        return {"verified": False, "distance": 1.0, "reason": str(e)}