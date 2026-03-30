from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.upload import router as upload_router
from api.ocr import router as ocr_router
from api.extract import router as extract_router
from api.compliance import router as compliance_router
from api.summary import router as summary_router
from api.logs import router as logs_router
from api.reports import router as reports_router
from api.stats import router as stats_router
from api.auth import router as auth_router
from api.cases import router as cases_router
from api.admin import router as admin_router
from api.health import router as health_router
from database.db import init_db, restore_remote_data_if_configured
from utils.firebase_service import initialize_firebase

app = FastAPI(title="AI-Based Intelligent Document Processing and Compliance Automation System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/upload", tags=["upload"])
app.include_router(ocr_router, prefix="/ocr", tags=["ocr"])
app.include_router(extract_router, prefix="/extract", tags=["extract"])
app.include_router(compliance_router, prefix="/compliance", tags=["compliance"])
app.include_router(summary_router, prefix="/summary", tags=["summary"])
app.include_router(logs_router, prefix="/logs", tags=["logs"])
app.include_router(reports_router, prefix="/reports", tags=["reports"])
app.include_router(stats_router, prefix="/stats", tags=["stats"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(cases_router, prefix="/cases", tags=["cases"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(health_router, prefix="/health", tags=["health"])

@app.on_event("startup")
async def on_startup():
    init_db()
    initialize_firebase()
    restore_remote_data_if_configured()
