#!/usr/bin/env python3
"""
Simple backend startup script that handles import paths correctly.
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

# Change to backend directory
os.chdir(project_root / "backend")

# Now import and run
if __name__ == "__main__":
    import uvicorn
    from main import app
    
    print("🚀 Starting AI Case Documentation Backend...")
    print("📁 Project root:", project_root)
    print("📂 Working directory:", os.getcwd())
    print("🔗 Backend URL: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
