import re
from typing import List, Dict
from transformers import AutoProcessor, AutoModelForTokenClassification
import torch
from utils.confidence import clamp_confidence

# LayoutLMv3 is used for key-value extraction. This code attempts to load the model
# and falls back to a light heuristic when running without GPU or model weights.

_MODEL = None
_PROCESSOR = None


def _load_layoutlm():
    global _MODEL, _PROCESSOR
    if _MODEL is None or _PROCESSOR is None:
        _PROCESSOR = AutoProcessor.from_pretrained("microsoft/layoutlmv3-base")
        _MODEL = AutoModelForTokenClassification.from_pretrained("microsoft/layoutlmv3-base")
        _MODEL.eval()
    return _MODEL, _PROCESSOR


def _heuristic_extract(text: str) -> List[Dict]:
    # Simple regex fallback: not a replacement for LayoutLMv3, but keeps the pipeline runnable.
    fields = {
        "Invoice No": r"Invoice\s*No\.?\s*[:#]?\s*([A-Za-z0-9-]+)",
        "Date": r"Date\s*[:]?\s*([0-9]{2}[/-][0-9]{2}[/-][0-9]{2,4})",
        "Amount": r"Total\s*Amount\s*[:$]?\s*([0-9,]+\.?[0-9]{0,2})",
        "Vendor": r"Vendor\s*[:]?\s*([A-Za-z0-9 &.-]+)",
        "Signature": r"Signature\s*[:]?\s*([A-Za-z ]+)",
    }

    results = []
    for field, pattern in fields.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            results.append({"field": field, "value": match.group(1).strip(), "confidence": clamp_confidence(0.65)})
        else:
            results.append({"field": field, "value": "", "confidence": clamp_confidence(0.0)})
    return results


def extract_key_values(image_path: str, text: str) -> List[Dict]:
    # Full LayoutLMv3 pipeline would require word-level boxes from OCR and detailed mapping.
    # We attempt model loading, but keep a safe fallback for local dev.
    try:
        _load_layoutlm()
    except Exception:
        return _heuristic_extract(text)

    # Placeholder inference for local demo; use heuristic with a note.
    # In a full pipeline, pass word boxes and use model logits for token classification.
    return _heuristic_extract(text)
