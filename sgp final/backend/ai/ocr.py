import os
import shutil
from pathlib import Path
from typing import Dict, List

import cv2
import pytesseract
from PIL import Image
import numpy as np

# Optional dependencies for PDF/DOCX support
try:
    from pdf2image import convert_from_path
except Exception:  # pragma: no cover - optional dependency
    convert_from_path = None

try:
    from docx import Document as DocxDocument
except Exception:  # pragma: no cover - optional dependency
    DocxDocument = None

try:
    from ai.transcriber import transcribe_audio
except Exception:  # pragma: no cover - optional dependency
    transcribe_audio = None

# OCR step: use Tesseract for text + bounding boxes.
# EasyOCR can be added as a drop-in replacement or fallback if needed.

AUDIO_EXTENSIONS = {
    ".wav", ".mp3", ".m4a", ".flac", ".aac", ".ogg", ".opus", ".wma", ".webm", ".mp4", ".mpeg"
}


def _resolve_tesseract_cmd() -> str | None:
    env_cmd = os.getenv("TESSERACT_CMD")
    if env_cmd and os.path.exists(env_cmd):
        return env_cmd

    found = shutil.which("tesseract")
    if found:
        return found

    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return None


def _resolve_poppler_path() -> str | None:
    env_path = os.getenv("POPPLER_PATH")
    if env_path and os.path.exists(env_path):
        return env_path

    pdfinfo_path = shutil.which("pdfinfo")
    if pdfinfo_path:
        return str(Path(pdfinfo_path).parent)

    candidates = [
        r"C:\Program Files\poppler\Library\bin",
        r"C:\Program Files (x86)\poppler\Library\bin",
    ]

    winget_root = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    if winget_root.exists():
        winget_matches = sorted(
            winget_root.glob("oschwartz10612.Poppler*/poppler-*/Library/bin"),
            reverse=True,
        )
        candidates.extend([str(path) for path in winget_matches])

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return None


def _configure_ocr_dependencies() -> None:
    tesseract_cmd = _resolve_tesseract_cmd()
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd


def preprocess_array(image: np.ndarray) -> np.ndarray:
    if image is None:
        raise ValueError("Image not found or unsupported format")

    # Resize to a consistent width for better OCR on small scans
    target_width = 1800
    h, w = image.shape[:2]
    if w < target_width:
        scale = target_width / float(w)
        image = cv2.resize(image, (target_width, int(h * scale)), interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    return gray


def preprocess_image(image_path: str) -> np.ndarray:
    image = cv2.imread(image_path)
    return preprocess_array(image)


def _ocr_image_array(image: np.ndarray, page_index: int = 0) -> Dict:
    _configure_ocr_dependencies()
    processed = preprocess_array(image)
    pil_img = Image.fromarray(processed)
    try:
        data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
    except pytesseract.TesseractNotFoundError as exc:
        raise ValueError(
            "Tesseract executable not found. Install Tesseract and set PATH or TESSERACT_CMD."
        ) from exc
    text = " ".join([word for word in data["text"] if word.strip()])
    boxes: List[Dict] = []
    for i in range(len(data["text"])):
        if data["text"][i].strip():
            boxes.append({
                "text": data["text"][i],
                "left": data["left"][i],
                "top": data["top"][i],
                "width": data["width"][i],
                "height": data["height"][i],
                "page": page_index,
            })
    return {"text": text, "boxes": boxes}


def perform_ocr(file_path: str):
    _configure_ocr_dependencies()
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        if convert_from_path is None:
            raise ValueError("pdf2image is not installed. Install it to OCR PDFs.")
        poppler_path = _resolve_poppler_path()
        convert_kwargs = {"dpi": 300}
        if poppler_path:
            convert_kwargs["poppler_path"] = poppler_path
        pages = convert_from_path(file_path, **convert_kwargs)
        full_text = []
        all_boxes = []
        for idx, page in enumerate(pages):
            image = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
            result = _ocr_image_array(image, page_index=idx)
            full_text.append(result["text"])
            all_boxes.extend(result["boxes"])
        return {"text": "\n".join(full_text), "boxes": all_boxes}

    if ext == ".docx":
        if DocxDocument is None:
            raise ValueError("python-docx is not installed. Install it to parse DOCX.")
        doc = DocxDocument(file_path)
        text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        return {"text": text, "boxes": []}

    if ext in [".txt", ".md"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return {"text": f.read(), "boxes": []}

    if ext in AUDIO_EXTENSIONS:
        if transcribe_audio is None:
            raise ValueError(
                "Audio transcription is not configured. Install openai-whisper and ffmpeg, then restart backend."
            )
        text = transcribe_audio(file_path)
        if not (text or "").strip():
            raise ValueError("Audio transcription produced empty text.")
        return {"text": text, "boxes": []}

    image = cv2.imread(file_path)
    if image is None:
        raise ValueError("Unsupported file type for OCR.")
    return _ocr_image_array(image, page_index=0)
