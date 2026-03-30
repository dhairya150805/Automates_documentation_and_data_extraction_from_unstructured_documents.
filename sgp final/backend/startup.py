"""
Minimal backend startup with better error handling
"""
import sys
import traceback
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path.cwd()))

print("🚀 Starting AI Case Documentation Backend...")
print(f"📂 Working directory: {Path.cwd()}")

try:
    print("📦 Testing imports...")
    from fastapi import FastAPI
    print("✅ FastAPI imported")
    
    from main import app
    print("✅ Main app imported")
    
    import uvicorn
    print("✅ Uvicorn imported")
    
    print("🌐 Starting server on http://0.0.0.0:8000")
    print("📖 API Docs available at: http://localhost:8000/docs")
    print("🔍 Health check: http://localhost:8000/health/")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
    
except Exception as e:
    print(f"❌ Startup failed: {e}")
    print("📋 Full traceback:")
    traceback.print_exc()
    sys.exit(1)
