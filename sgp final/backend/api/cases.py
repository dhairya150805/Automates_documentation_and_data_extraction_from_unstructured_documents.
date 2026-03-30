from datetime import datetime
import io
import csv
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Case, Document, ExtractedData, ComplianceResult, AuditLog, User
from utils.case_summary import build_case_summary
from ai.ocr import perform_ocr
from ai.layoutlm import extract_key_values
from ai.summarizer import summarize_text
from utils.compliance_rules import evaluate_compliance
from utils.document_storage import get_accessible_file_path
from utils.firebase_service import (
    sync_case_record,
    sync_doc_record,
    sync_audit_record,
    sync_extracted_record,
    sync_compliance_record,
)

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except Exception:  # pragma: no cover - optional dependency
    canvas = None
    letter = None

router = APIRouter()


@router.post("/")
async def create_case(payload: dict, user_id: int, db: Session = Depends(get_db)):
    title = (payload.get("title") or "").strip()
    description = (payload.get("description") or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Case title is required.")
    owner = db.query(User).filter(User.id == user_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="User not found.")

    case = Case(
        user_id=user_id,
        title=title,
        description=description or None,
        created_at=datetime.utcnow(),
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    sync_case_record(case)
    return {
        "status": "success",
        "case_id": case.id,
        "title": case.title,
        "description": case.description,
        "created_at": case.created_at.isoformat(),
    }


@router.get("/")
async def list_cases(
    user_id: int,
    page: int = 1,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    page = max(page, 1)
    limit = min(max(limit, 1), 200)
    base_query = db.query(Case).filter(Case.user_id == user_id)
    total = base_query.count()
    cases = (
        base_query
        .order_by(Case.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return {
        "cases": [
            {
                "case_id": c.id,
                "title": c.title,
                "description": c.description,
                "created_at": c.created_at.isoformat(),
            }
            for c in cases
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/{case_id}")
async def get_case(case_id: int, user_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id, Case.user_id == user_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    docs = db.query(Document).filter(Document.case_id == case.id, Document.user_id == user_id).all()
    return {
        "case_id": case.id,
        "title": case.title,
        "description": case.description,
        "created_at": case.created_at.isoformat(),
        "evidence_count": len(docs),
    }


@router.get("/{case_id}/summary")
async def get_case_summary(case_id: int, user_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id, Case.user_id == user_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    docs = db.query(Document).filter(Document.case_id == case.id, Document.user_id == user_id).all()
    doc_ids = [d.id for d in docs]
    extracted_rows = db.query(ExtractedData).filter(ExtractedData.doc_id.in_(doc_ids)).all() if docs else []
    compliance_rows = db.query(ComplianceResult).filter(ComplianceResult.doc_id.in_(doc_ids)).all() if docs else []

    extracted_lookup = {}
    for row in extracted_rows:
        extracted_lookup.setdefault(row.doc_id, []).append(row)

    compliance_lookup = {row.doc_id: row for row in compliance_rows}

    return build_case_summary(case, docs, extracted_lookup, compliance_lookup)


@router.post("/{case_id}/process")
async def process_case(case_id: int, payload: dict, user_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id, Case.user_id == user_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    rules = payload.get("rules")
    run_compliance = bool(payload.get("run_compliance"))
    force = bool(payload.get("force"))

    docs = db.query(Document).filter(Document.case_id == case.id, Document.user_id == user_id).all()
    if not docs:
        raise HTTPException(status_code=400, detail="No documents found for this case.")

    results = []
    for doc in docs:
        try:
            if force or not doc.ocr_text:
                processing_path = get_accessible_file_path(doc)
                ocr_result = perform_ocr(processing_path)
                doc.ocr_text = ocr_result.get("text", "")
                db.commit()
                db.refresh(doc)
                sync_doc_record(doc)

            if force or not db.query(ExtractedData).filter(ExtractedData.doc_id == doc.id).first():
                if not doc.ocr_text:
                    raise ValueError("OCR text is missing. Run OCR first.")
                processing_path = get_accessible_file_path(doc)
                extracted = extract_key_values(processing_path, doc.ocr_text)
                db.query(ExtractedData).filter(ExtractedData.doc_id == doc.id).delete()
                for item in extracted:
                    db.add(ExtractedData(
                        doc_id=doc.id,
                        field=item["field"],
                        value=item["value"],
                        confidence=item["confidence"],
                    ))
                db.commit()
                refreshed = db.query(ExtractedData).filter(ExtractedData.doc_id == doc.id).all()
                for item in refreshed:
                    sync_extracted_record(item)

            if force or not doc.summary:
                if not doc.ocr_text:
                    raise ValueError("OCR text is missing. Run OCR first.")
                doc.summary = summarize_text(doc.ocr_text)
                db.commit()
                db.refresh(doc)
                sync_doc_record(doc)

            compliance = None
            if run_compliance and isinstance(rules, dict):
                extracted_rows = db.query(ExtractedData).filter(ExtractedData.doc_id == doc.id).all()
                extracted_map = {e.field: e.value for e in extracted_rows}
                compliance = evaluate_compliance(extracted_map, rules)
                db.query(ComplianceResult).filter(ComplianceResult.doc_id == doc.id).delete()
                db.add(ComplianceResult(
                    doc_id=doc.id,
                    status=compliance["status"],
                    remarks=compliance["remarks"],
                ))
                db.commit()
                compliance_row = db.query(ComplianceResult).filter(ComplianceResult.doc_id == doc.id).first()
                if compliance_row:
                    sync_compliance_record(compliance_row)

            audit = AuditLog(
                user_id=doc.user_id,
                action=f"Case processing pipeline run for document {doc.filename} (case {case.id})",
                timestamp=datetime.utcnow(),
            )
            db.add(audit)
            db.commit()
            db.refresh(audit)
            sync_audit_record(audit)

            results.append({
                "doc_id": doc.id,
                "filename": doc.filename,
                "compliance": compliance,
            })
        except Exception as exc:
            results.append({
                "doc_id": doc.id,
                "filename": doc.filename,
                "error": str(exc),
            })

    return {
        "status": "success",
        "case_id": case.id,
        "processed": results,
    }


def _build_case_csv(case, summary):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["case_id", "title", "description", "created_at"])
    writer.writerow([case.id, case.title, case.description or "", case.created_at.isoformat()])
    writer.writerow([])
    writer.writerow(["evidence_count", summary.get("evidence_count", 0)])
    writer.writerow([])
    writer.writerow(["Evidence"])
    writer.writerow(["doc_id", "filename", "file_type", "doc_type", "upload_time"])
    for item in summary.get("evidence", []):
        writer.writerow([item["doc_id"], item["filename"], item["file_type"], item["doc_type"], item["upload_time"]])
    writer.writerow([])
    writer.writerow(["Aggregated Fields"])
    writer.writerow(["field", "best_value", "confidence", "doc_id"])
    for field, data in summary.get("aggregated_fields", {}).items():
        best = data.get("best", {})
        writer.writerow([field, best.get("value"), best.get("confidence"), best.get("doc_id")])
    return output.getvalue()


def _build_case_pdf(case, summary):
    if canvas is None:
        raise ValueError("reportlab is not installed. Install it to generate PDFs.")

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Case Summary Report")
    y -= 30

    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Case ID: {case.id}")
    y -= 15
    c.drawString(40, y, f"Title: {case.title}")
    y -= 15
    c.drawString(40, y, f"Description: {case.description or ''}")
    y -= 15
    c.drawString(40, y, f"Created: {case.created_at.isoformat()}")
    y -= 25

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Evidence")
    y -= 18
    c.setFont("Helvetica", 10)
    for item in summary.get("evidence", []):
        c.drawString(50, y, f"{item['doc_id']}: {item['filename']} ({item['file_type']})")
        y -= 14
        if y < 60:
            c.showPage()
            y = height - 40

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Aggregated Fields")
    y -= 18
    c.setFont("Helvetica", 10)
    for field, data in summary.get("aggregated_fields", {}).items():
        best = data.get("best", {})
        c.drawString(50, y, f"{field}: {best.get('value')} (conf: {best.get('confidence')})")
        y -= 14
        if y < 60:
            c.showPage()
            y = height - 40

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()


@router.get("/{case_id}/report")
async def get_case_report(case_id: int, user_id: int, format: str = "csv", db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id, Case.user_id == user_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    docs = db.query(Document).filter(Document.case_id == case.id, Document.user_id == user_id).all()
    extracted_rows = db.query(ExtractedData).filter(ExtractedData.doc_id.in_([d.id for d in docs])).all() if docs else []
    compliance_rows = db.query(ComplianceResult).filter(ComplianceResult.doc_id.in_([d.id for d in docs])).all() if docs else []

    extracted_lookup = {}
    for row in extracted_rows:
        extracted_lookup.setdefault(row.doc_id, []).append(row)
    compliance_lookup = {row.doc_id: row for row in compliance_rows}

    summary = build_case_summary(case, docs, extracted_lookup, compliance_lookup)

    if format.lower() == "csv":
        csv_data = _build_case_csv(case, summary)
        filename = f"case_{case.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
        return StreamingResponse(
            io.BytesIO(csv_data.encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    if format.lower() == "pdf":
        try:
            pdf_bytes = _build_case_pdf(case, summary)
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc))
        filename = f"case_{case.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    raise HTTPException(status_code=400, detail="Unsupported format. Use csv or pdf.")
