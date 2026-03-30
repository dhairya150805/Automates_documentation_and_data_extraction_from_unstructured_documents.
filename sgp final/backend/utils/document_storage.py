import os
from pathlib import Path

from utils.firebase_service import download_to_file

CACHE_DIR = Path(__file__).resolve().parent.parent / "storage_cache"


def get_accessible_file_path(doc) -> str:
    if doc.file_path and os.path.exists(doc.file_path):
        return doc.file_path

    storage_provider = getattr(doc, "storage_provider", None)
    storage_path = getattr(doc, "storage_path", None)
    if storage_provider == "firebase" and storage_path:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        storage_suffix = Path(storage_path).suffix
        if storage_suffix:
            extension = storage_suffix
        elif getattr(doc, "file_type", None):
            extension = f".{str(doc.file_type).lstrip('.')}"
        else:
            extension = ""

        # Use stable extension to preserve downstream file-type detection (OCR/transcription routing).
        target = CACHE_DIR / f"{doc.id}{extension}"
        if not target.exists():
            if not download_to_file(storage_path, str(target)):
                raise FileNotFoundError("Document not found locally and Firebase download is unavailable.")
        doc.file_path = str(target)
        return doc.file_path

    raise FileNotFoundError("Document file path is not accessible.")
