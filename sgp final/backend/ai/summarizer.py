import re

from transformers import pipeline

# Pre-trained summarizer (no training). Uses BART for concise summaries.

_summarizer = None
_summarizer_mode = None


def _fallback_summary(text: str) -> str:
    cleaned = " ".join((text or "").split())
    if not cleaned:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    if not parts:
        return cleaned[:500]
    return " ".join(parts[:3])[:500]


def _get_summarizer():
    global _summarizer, _summarizer_mode
    if _summarizer is not None:
        return _summarizer, _summarizer_mode

    # Newer transformers builds can expose text2text-generation without summarization alias.
    task_candidates = ["summarization", "text2text-generation"]
    for task in task_candidates:
        try:
            _summarizer = pipeline(task, model="facebook/bart-large-cnn")
            _summarizer_mode = task
            return _summarizer, _summarizer_mode
        except Exception:
            continue

    _summarizer = None
    _summarizer_mode = "fallback"
    return None, _summarizer_mode


def summarize_text(text: str) -> str:
    trimmed = (text or "")[:4000]
    if not trimmed.strip():
        return ""

    summarizer, mode = _get_summarizer()
    if summarizer is None or mode == "fallback":
        return _fallback_summary(trimmed)

    token_estimate = max(1, len(trimmed.split()))
    min_len = max(5, min(30, token_estimate // 6))
    max_len = max(min_len + 10, min(120, token_estimate // 2))

    try:
        result = summarizer(trimmed, max_length=max_len, min_length=min_len, do_sample=False)
        first = result[0] if result else {}
        return first.get("summary_text") or first.get("generated_text") or _fallback_summary(trimmed)
    except Exception:
        return _fallback_summary(trimmed)
