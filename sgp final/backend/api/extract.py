from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import Document, ExtractedData, AuditLog
from ai.layoutlm import extract_key_values
from datetime import datetime
from utils.document_storage import get_accessible_file_path
from utils.firebase_service import sync_audit_record, sync_extracted_record

router = APIRouter()

@router.post("/")
async def extract(doc_id: int, user_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == user_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not doc.ocr_text:
        raise HTTPException(status_code=400, detail="OCR text is missing. Run OCR first.")

    try:
        processing_path = get_accessible_file_path(doc)
        results = extract_key_values(processing_path, doc.ocr_text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {exc}")

    db.query(ExtractedData).filter(ExtractedData.doc_id == doc.id).delete()

    for item in results:
        db.add(ExtractedData(
            doc_id=doc.id,
            field=item["field"],
            value=item["value"],
            confidence=item["confidence"],
        ))

    db.commit()
    saved = db.query(ExtractedData).filter(ExtractedData.doc_id == doc.id).all()
    for item in saved:
        sync_extracted_record(item)

    log = AuditLog(user_id=doc.user_id, action=f"Extraction performed on document {doc.filename}", timestamp=datetime.utcnow())
    db.add(log)
    db.commit()
    db.refresh(log)
    sync_audit_record(log)

    return {
        "status": "success",
        "doc_id": doc.id,
        "extracted_data": results,
    }


@router.put("/")
async def update_extracted(doc_id: int, payload: dict, user_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == user_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    extracted_data = payload.get("extracted_data")
    if not isinstance(extracted_data, list):
        raise HTTPException(status_code=400, detail="extracted_data must be a list")

    db.query(ExtractedData).filter(ExtractedData.doc_id == doc.id).delete()
    for item in extracted_data:
        field = (item.get("field") or "").strip()
        value = (item.get("value") or "").strip()
        confidence = float(item.get("confidence") or 0)
        if not field:
            continue
        db.add(ExtractedData(
            doc_id=doc.id,
            field=field,
            value=value,
            confidence=confidence,
        ))
    db.commit()
    saved = db.query(ExtractedData).filter(ExtractedData.doc_id == doc.id).all()
    for item in saved:
        sync_extracted_record(item)

    audit = AuditLog(
        user_id=doc.user_id,
        action=f"Manual extraction review for document {doc.filename}",
        timestamp=datetime.utcnow(),
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    sync_audit_record(audit)

    return {
        "status": "success",
        "doc_id": doc.id,
        "message": "Extracted data updated.",
    }
