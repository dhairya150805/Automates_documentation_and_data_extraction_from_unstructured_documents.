from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import AuditLog

router = APIRouter()

@router.get("/")
async def get_logs(user_id: int, db: Session = Depends(get_db)):
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.user_id == user_id)
        .order_by(AuditLog.timestamp.desc())
        .limit(200)
        .all()
    )
    return [
        {
            "user_id": log.user_id,
            "action": log.action,
            "timestamp": log.timestamp.isoformat(),
        }
        for log in logs
    ]
