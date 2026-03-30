import os
import shutil
from pathlib import Path

try:
    import whisper
except Exception:  # pragma: no cover - optional dependency
    whisper = None

_MODEL = None


def _resolve_ffmpeg_cmd() -> str | None:
    env_cmd = os.getenv("FFMPEG_CMD")
    if env_cmd and os.path.exists(env_cmd):
        return env_cmd

    found = shutil.which("ffmpeg")
    if found:
        return found

    candidates = [
        r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
    ]

    winget_links = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe"
    candidates.append(str(winget_links))

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return None


def _configure_whisper_ffmpeg() -> None:
    if whisper is None:
        return
    ffmpeg_cmd = _resolve_ffmpeg_cmd()
    if not ffmpeg_cmd:
        raise ValueError(
            "FFmpeg executable not found. Install FFmpeg and add it to PATH, "
            "or set FFMPEG_CMD to the full ffmpeg.exe path."
        )

    ffmpeg_dir = str(Path(ffmpeg_cmd).parent)
    current_path = os.environ.get("PATH", "")
    path_parts = current_path.split(os.pathsep) if current_path else []
    if ffmpeg_dir not in path_parts:
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + current_path

    try:
        import whisper.audio as whisper_audio
        if hasattr(whisper_audio, "FFMPEG"):
            whisper_audio.FFMPEG = ffmpeg_cmd
    except Exception:
        pass


def transcribe_audio(file_path: str) -> str:
    if whisper is None:
        raise ValueError("Audio transcription requires openai-whisper and ffmpeg.")
    if not os.path.exists(file_path):
        raise ValueError(f"Audio file not found: {file_path}")

    _configure_whisper_ffmpeg()

    global _MODEL
    if _MODEL is None:
        _MODEL = whisper.load_model("base")

    try:
        result = _MODEL.transcribe(file_path)
    except FileNotFoundError as exc:
        raise ValueError(
            "FFmpeg is not accessible by backend process. Install FFmpeg and ensure PATH is updated, "
            "or set FFMPEG_CMD to ffmpeg.exe."
        ) from exc
    return result.get("text", "")
