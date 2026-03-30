from fastapi import APIRouter, HTTPException
import os
import subprocess
import sys
from datetime import datetime

router = APIRouter()

@router.get("/")
async def system_health():
    """Get system health status and configuration"""
    
    health_status = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "healthy",
        "services": {},
        "dependencies": {},
        "storage": {},
        "warnings": []
    }
    
    # Check Python version
    health_status["services"]["python"] = {
        "version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "status": "ok"
    }
    
    # Check AI dependencies
    try:
        import pytesseract
        health_status["dependencies"]["tesseract"] = {"status": "ok", "version": "available"}
    except ImportError:
        health_status["dependencies"]["tesseract"] = {"status": "error", "message": "Tesseract OCR not found"}
        health_status["warnings"].append("Tesseract OCR is not installed - text extraction will fail")
    
    try:
        import whisper
        health_status["dependencies"]["whisper"] = {"status": "ok", "version": "available"}
    except ImportError:
        health_status["dependencies"]["whisper"] = {"status": "error", "message": "OpenAI Whisper not found"}
        health_status["warnings"].append("OpenAI Whisper is not installed - audio transcription will fail")
    
    try:
        import transformers
        health_status["dependencies"]["transformers"] = {"status": "ok", "version": "available"}
    except ImportError:
        health_status["dependencies"]["transformers"] = {"status": "error", "message": "Transformers not found"}
        health_status["warnings"].append("Transformers library missing - LayoutLM extraction will fail")
    
    # Check FFmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            health_status["dependencies"]["ffmpeg"] = {"status": "ok", "version": "available"}
        else:
            health_status["dependencies"]["ffmpeg"] = {"status": "error", "message": "FFmpeg not working properly"}
            health_status["warnings"].append("FFmpeg is not working - audio processing will fail")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        health_status["dependencies"]["ffmpeg"] = {"status": "error", "message": "FFmpeg not found in PATH"}
        health_status["warnings"].append("FFmpeg is not installed - audio transcription will fail")
    
    # Check storage directory
    storage_dir = os.path.join(os.path.dirname(__file__), "..", "storage")
    if os.path.exists(storage_dir):
        try:
            files = os.listdir(storage_dir)
            storage_size = sum(os.path.getsize(os.path.join(storage_dir, f)) for f in files if os.path.isfile(os.path.join(storage_dir, f)))
            health_status["storage"] = {
                "status": "ok",
                "path": storage_dir,
                "files_count": len(files),
                "total_size_mb": round(storage_size / (1024 * 1024), 2)
            }
        except Exception as e:
            health_status["storage"] = {"status": "error", "message": str(e)}
    else:
        health_status["storage"] = {"status": "warning", "message": "Storage directory does not exist"}
        health_status["warnings"].append("Storage directory missing - file uploads may fail")
      # Check database
    try:
        from database.db import engine, get_database_info
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_info = get_database_info()
            health_status["services"]["database"] = {
                "status": "ok",
                "type": db_info["dialect"],
                "url": db_info["url"],
            }
            if db_info["dialect"] == "sqlite":
                health_status["services"]["database"]["path"] = db_info.get("default_path")
    except Exception as e:
        health_status["services"]["database"] = {"status": "error", "message": str(e)}
        health_status["warnings"].append("Database connection failed")

    try:
        from utils.firebase_service import get_firebase_status
        firebase_status = get_firebase_status()
        health_status["services"]["firebase"] = {
            "status": "ok" if firebase_status.get("enabled") else "not_configured",
            "storage_bucket": firebase_status.get("storage_bucket"),
            "message": firebase_status.get("error"),
        }
        if not firebase_status.get("enabled"):
            health_status["warnings"].append("Firebase is not configured - cloud persistence is disabled")
    except Exception as e:
        health_status["services"]["firebase"] = {"status": "error", "message": str(e)}
        health_status["warnings"].append("Firebase health check failed")
    
    # Determine overall status
    has_errors = any(
        dep.get("status") == "error" 
        for dep in health_status["dependencies"].values()
    ) or any(
        service.get("status") == "error" 
        for service in health_status["services"].values()
    )
    
    if has_errors:
        health_status["status"] = "degraded"
    elif health_status["warnings"]:
        health_status["status"] = "warning"
    
    return health_status
