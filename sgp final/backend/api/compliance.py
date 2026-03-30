from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import Document, ExtractedData, ComplianceResult, AuditLog
from utils.compliance_rules import evaluate_compliance
from datetime import datetime
from utils.firebase_service import sync_audit_record, sync_compliance_record

router = APIRouter()

@router.post("/")
async def compliance(doc_id: int, rules: dict, user_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == user_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    extracted = db.query(ExtractedData).filter(ExtractedData.doc_id == doc.id).all()
    if not extracted:
        raise HTTPException(status_code=400, detail="No extracted data found. Run extraction first.")

    extracted_map = {e.field: e.value for e in extracted}
    result = evaluate_compliance(extracted_map, rules)

    db.query(ComplianceResult).filter(ComplianceResult.doc_id == doc.id).delete()
    db.add(ComplianceResult(
        doc_id=doc.id,
        status=result["status"],
        remarks=result["remarks"],
    ))
    db.commit()
    compliance_row = db.query(ComplianceResult).filter(ComplianceResult.doc_id == doc.id).first()
    if compliance_row:
        sync_compliance_record(compliance_row)

    log = AuditLog(user_id=doc.user_id, action=f"Compliance check performed on document {doc.filename}", timestamp=datetime.utcnow())
    db.add(log)
    db.commit()
    db.refresh(log)
    sync_audit_record(log)

    return {
        "status": "success",
        "doc_id": doc.id,
        "compliance": result,
    }
