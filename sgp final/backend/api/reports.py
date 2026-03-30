import io
import csv
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Document, ExtractedData, ComplianceResult, AuditLog
from utils.firebase_service import sync_audit_record

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except Exception:  # pragma: no cover - optional dependency
    canvas = None
    letter = None

router = APIRouter()


def _build_csv(doc: Document, extracted, compliance):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["doc_id", "filename", "doc_type", "upload_time"])
    writer.writerow([doc.id, doc.filename, doc.doc_type, doc.upload_time.isoformat()])
    writer.writerow([])
    writer.writerow(["field", "value", "confidence"])
    for item in extracted:
        writer.writerow([item.field, item.value, item.confidence])
    writer.writerow([])
    writer.writerow(["compliance_status", "remarks"])
    if compliance:
        writer.writerow([compliance.status, compliance.remarks])
    else:
        writer.writerow(["N/A", "No compliance results"])
    writer.writerow([])
    writer.writerow(["summary"])
    writer.writerow([doc.summary or ""])
    return output.getvalue()


def _build_pdf(doc: Document, extracted, compliance):
    if canvas is None:
        raise ValueError("reportlab is not installed. Install it to generate PDFs.")

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Document Processing Report")
    y -= 30

    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Document ID: {doc.id}")
    y -= 15
    c.drawString(40, y, f"Filename: {doc.filename}")
    y -= 15
    c.drawString(40, y, f"Type: {doc.doc_type}")
    y -= 15
    c.drawString(40, y, f"Uploaded: {doc.upload_time.isoformat()}")
    y -= 25

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Extracted Fields")
    y -= 18
    c.setFont("Helvetica", 10)
    for item in extracted:
        c.drawString(50, y, f"{item.field}: {item.value} (conf: {item.confidence})")
        y -= 14
        if y < 60:
            c.showPage()
            y = height - 40

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Compliance")
    y -= 18
    c.setFont("Helvetica", 10)
    if compliance:
        c.drawString(50, y, f"Status: {compliance.status}")
        y -= 14
        c.drawString(50, y, f"Remarks: {compliance.remarks}")
    else:
        c.drawString(50, y, "No compliance results")
    y -= 24

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Summary")
    y -= 18
    c.setFont("Helvetica", 10)
    summary_lines = (doc.summary or "").splitlines() or [""]
    for line in summary_lines:
        c.drawString(50, y, line[:120])
        y -= 14
        if y < 60:
            c.showPage()
            y = height - 40

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()


@router.get("/")
async def get_report(doc_id: int, user_id: int, format: str = "csv", db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.user_id == user_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    extracted = db.query(ExtractedData).filter(ExtractedData.doc_id == doc.id).all()
    compliance = db.query(ComplianceResult).filter(ComplianceResult.doc_id == doc.id).first()

    log = AuditLog(user_id=doc.user_id, action=f"Report generated ({format}) for document {doc.filename}", timestamp=datetime.utcnow())
    db.add(log)
    db.commit()
    db.refresh(log)
    sync_audit_record(log)

    if format.lower() == "csv":
        csv_data = _build_csv(doc, extracted, compliance)
        filename = f"report_{doc.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
        return StreamingResponse(
            io.BytesIO(csv_data.encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    if format.lower() == "pdf":
        try:
            pdf_bytes = _build_pdf(doc, extracted, compliance)
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc))
        filename = f"report_{doc.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    raise HTTPException(status_code=400, detail="Unsupported format. Use csv or pdf.")
