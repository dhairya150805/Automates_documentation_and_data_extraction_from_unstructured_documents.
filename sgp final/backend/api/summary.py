from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import Document, AuditLog
from ai.summarizer import summarize_text
from datetime import datetime
from utils.firebase_service import sync_audit_record, sync_doc_record

router = APIRouter()

@router.post("/")
async def summary(doc_id: int, user_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == user_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not doc.ocr_text:
        raise HTTPException(status_code=400, detail="OCR text is missing. Run OCR first.")

    try:
        summary_text = summarize_text(doc.ocr_text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {exc}")

    doc.summary = summary_text
    db.commit()
    db.refresh(doc)
    sync_doc_record(doc)

    log = AuditLog(user_id=doc.user_id, action=f"Summary generated for document {doc.filename}", timestamp=datetime.utcnow())
    db.add(log)
    db.commit()
    db.refresh(log)
    sync_audit_record(log)

    return {
        "status": "success",
        "doc_id": doc.id,
        "summary": summary_text,
    }
