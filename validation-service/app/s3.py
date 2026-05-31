import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

def save_file_locally(file_content: bytes, file_name: str) -> str:
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file_name)
    with open(file_path, "wb") as f:
        f.write(file_content)
    return file_path

def get_file_path(file_name: str) -> str:
    return os.path.join(UPLOAD_DIR, file_name)

def save_parquet_locally(df, job_id: int) -> str:
    output_dir = os.path.join(UPLOAD_DIR, "output")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    output_path = os.path.join(output_dir, f"job_{job_id}_validated.parquet")
    df.to_parquet(output_path, index=False)
    return output_path