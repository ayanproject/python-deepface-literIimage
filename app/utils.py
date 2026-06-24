import os
import tempfile
from typing import Optional

def save_bytes_to_tempfile(bytes_data: bytes, suffix: str = ".jpg") -> str:
    """
    Save bytes to a NamedTemporaryFile and return the file path.
    Caller is responsible for deleting file when done.
    """
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tf.write(bytes_data)
    tf.flush()
    tf.close()
    return tf.name

def local_test_file_path(voter_id: int, local_dir: str) -> Optional[str]:
    """
    Return path to local test JPG if present, else None.
    Example: ./test_data/1.jpg
    """
    fname = os.path.join(local_dir, f"{voter_id}.jpg")
    return fname if os.path.isfile(fname) else None