from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.db import get_db
from database.models import Document, ComplianceResult, Case

router = APIRouter()


@router.get("/")
async def get_stats(user_id: int, db: Session = Depends(get_db)):
    user_docs_query = db.query(Document.id).filter(Document.user_id == user_id)

    total_docs = db.query(func.count(Document.id)).filter(Document.user_id == user_id).scalar() or 0
    pass_count = (
        db.query(func.count(ComplianceResult.id))
        .filter(ComplianceResult.status == "PASS", ComplianceResult.doc_id.in_(user_docs_query))
        .scalar()
        or 0
    )
    fail_count = (
        db.query(func.count(ComplianceResult.id))
        .filter(ComplianceResult.status == "FAIL", ComplianceResult.doc_id.in_(user_docs_query))
        .scalar()
        or 0
    )
    warn_count = (
        db.query(func.count(ComplianceResult.id))
        .filter(ComplianceResult.status == "WARNING", ComplianceResult.doc_id.in_(user_docs_query))
        .scalar()
        or 0
    )
    case_count = db.query(func.count(Case.id)).filter(Case.user_id == user_id).scalar() or 0

    return {
        "total_docs": total_docs,
        "pass": pass_count,
        "fail": fail_count,
        "warning": warn_count,
        "cases": case_count,
    }
