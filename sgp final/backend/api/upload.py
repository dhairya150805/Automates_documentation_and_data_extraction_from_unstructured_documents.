import os
from datetime import datetime

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import Document, AuditLog, Case, User
from utils.firebase_service import (
    upload_bytes,
    firebase_enabled,
    sync_doc_record,
    sync_audit_record,
    sync_case_record,
)

router = APIRouter()

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "storage")


@router.post("/")
async def upload_document(
    user_id: int,
    doc_type: str,
    case_id: int,
    display_name: str | None = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    os.makedirs(STORAGE_DIR, exist_ok=True)

    original_name = os.path.basename(file.filename or "uploaded_file")
    timestamped_filename = f"{int(datetime.utcnow().timestamp())}_{original_name}"
    file_path = os.path.join(STORAGE_DIR, timestamped_filename)
    original_ext = os.path.splitext(original_name)[1]
    file_type = original_ext.lower().lstrip(".") or "unknown"

    cleaned_display_name = (display_name or "").strip()
    if cleaned_display_name:
        safe_display_name = os.path.basename(cleaned_display_name)
        if original_ext and not os.path.splitext(safe_display_name)[1]:
            safe_display_name = f"{safe_display_name}{original_ext}"
    else:
        safe_display_name = original_name

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    if case.user_id is None:
        case.user_id = user_id
        db.commit()
        db.refresh(case)
        sync_case_record(case)
    if case.user_id is not None and case.user_id != user_id:
        raise HTTPException(status_code=403, detail="You cannot upload to another user's case.")

    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upload failed: {exc}")

    storage_provider = "local"
    storage_path = None
    storage_url = None
    if firebase_enabled():
        try:
            blob_path = f"uploads/user_{user_id}/case_{case_id}/{timestamped_filename}"
            uploaded = upload_bytes(blob_path, contents, content_type=file.content_type)
            if uploaded:
                storage_provider = "firebase"
                storage_path = uploaded.get("storage_path")
                storage_url = uploaded.get("storage_url")
        except Exception:
            storage_provider = "local"

    doc = Document(
        filename=safe_display_name,
        upload_time=datetime.utcnow(),
        user_id=user_id,
        case_id=case_id,
        doc_type=doc_type,
        file_type=file_type,
        file_path=file_path,
        storage_provider=storage_provider,
        storage_path=storage_path,
        storage_url=storage_url,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    sync_doc_record(doc)

    log = AuditLog(
        user_id=user_id,
        action=f"Uploaded document {safe_display_name} (case {case_id})",
        timestamp=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    sync_audit_record(log)

    return {
        "status": "success",
        "document_id": doc.id,
        "filename": safe_display_name,
        "doc_type": doc_type,
        "message": "File uploaded successfully",
    }
