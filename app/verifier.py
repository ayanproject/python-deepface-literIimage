import os
import urllib.request
import cv2
import numpy as np

# Directory to save model ONNX files
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
YUNET_URL = "https://huggingface.co/opencv/face_detection_yunet/resolve/main/face_detection_yunet_2023mar.onnx"
SFACE_URL = "https://huggingface.co/opencv/face_recognition_sface/resolve/main/face_recognition_sface_2021dec.onnx"

YUNET_PATH = os.path.join(MODELS_DIR, "face_detection_yunet_2023mar.onnx")
SFACE_PATH = os.path.join(MODELS_DIR, "face_recognition_sface_2021dec.onnx")

def download_models_if_missing():
    os.makedirs(MODELS_DIR, exist_ok=True)
    if not os.path.exists(YUNET_PATH):
        print(f"Downloading YuNet face detection model from {YUNET_URL}...")
        req = urllib.request.Request(
            YUNET_URL, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response, open(YUNET_PATH, 'wb') as out_file:
            out_file.write(response.read())
        print("YuNet model downloaded successfully.")
        
    if not os.path.exists(SFACE_PATH):
        print(f"Downloading SFace face recognition model from {SFACE_URL}...")
        req = urllib.request.Request(
            SFACE_URL, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response, open(SFACE_PATH, 'wb') as out_file:
            out_file.write(response.read())
        print("SFace model downloaded successfully.")

# Global references for detector and recognizer
detector = None
recognizer = None

def get_detector_and_recognizer():
    global detector, recognizer
    if detector is None or recognizer is None:
        download_models_if_missing()
        # Initialize detector with default size, size will be updated per image
        detector = cv2.FaceDetectorYN.create(YUNET_PATH, "", (320, 320))
        recognizer = cv2.FaceRecognizerSF.create(SFACE_PATH, "")
    return detector, recognizer

def verify_faces_by_path(probe_path: str, stored_path: str):
    """
    Loads images using OpenCV, generates facial encodings using YuNet/SFace,
    and returns a verification dictionary matching the original format.
    """
    try:
        det, rec = get_detector_and_recognizer()

        # Load images
        img_probe = cv2.imread(probe_path)
        img_stored = cv2.imread(stored_path)

        if img_probe is None or img_stored is None:
            return {"verified": False, "distance": 1.0, "reason": "Failed to load one or both images"}

        # 1. Detect face in probe image
        h1, w1, _ = img_probe.shape
        det.setInputSize((w1, h1))
        _, faces_probe = det.detect(img_probe)

        # 2. Detect face in stored image
        h2, w2, _ = img_stored.shape
        det.setInputSize((w2, h2))
        _, faces_stored = det.detect(img_stored)

        # Check if faces were detected in both
        if faces_probe is None or len(faces_probe) == 0:
            return {"verified": False, "distance": 1.0, "reason": "Face not detected in probe image"}
        if faces_stored is None or len(faces_stored) == 0:
            return {"verified": False, "distance": 1.0, "reason": "Face not detected in stored image"}

        # 3. Align and crop faces
        aligned_probe = rec.alignCrop(img_probe, faces_probe[0])
        aligned_stored = rec.alignCrop(img_stored, faces_stored[0])

        # 4. Extract feature vectors
        feat_probe = rec.feature(aligned_probe)
        feat_stored = rec.feature(aligned_stored)

        # 5. Compare faces using Cosine Similarity
        similarity = rec.match(feat_probe, feat_stored, cv2.FaceRecognizerSF_FR_COSINE)

        # A score >= 0.363 means they are the same person.
        verified = bool(similarity >= 0.363)

        return {
            "verified": verified,
            "distance": float(similarity)
        }
    except Exception as e:
        return {"verified": False, "distance": 1.0, "reason": str(e)}