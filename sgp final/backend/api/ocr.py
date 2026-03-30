from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import Document, AuditLog
from ai.ocr import perform_ocr
from datetime import datetime
from utils.document_storage import get_accessible_file_path
from utils.firebase_service import sync_doc_record, sync_audit_record

router = APIRouter()

@router.post("/")
async def run_ocr(doc_id: int, user_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == user_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        processing_path = get_accessible_file_path(doc)
        ocr_result = perform_ocr(processing_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OCR failed: {exc}")

    doc.ocr_text = ocr_result.get("text", "")
    db.commit()
    db.refresh(doc)
    sync_doc_record(doc)

    log = AuditLog(user_id=doc.user_id, action=f"OCR performed on document {doc.filename}", timestamp=datetime.utcnow())
    db.add(log)
    db.commit()
    db.refresh(log)
    sync_audit_record(log)

    return {
        "status": "success",
        "doc_id": doc.id,
        "text": ocr_result.get("text", ""),
        "boxes": ocr_result.get("boxes", []),
    }
