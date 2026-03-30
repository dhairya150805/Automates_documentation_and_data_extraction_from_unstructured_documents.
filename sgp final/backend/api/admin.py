import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import AuditLog, Case, ComplianceResult, Document, ExtractedData, User
from utils.firebase_service import (
    delete_audit_record,
    delete_case_record,
    delete_compliance_record,
    delete_doc_record,
    delete_extracted_record,
    delete_storage_blob,
    delete_user_record,
    sync_audit_record,
)

router = APIRouter()


def _require_admin(db: Session, user_id: int) -> User:
    actor = db.query(User).filter(User.id == user_id).first()
    if not actor:
        raise HTTPException(status_code=404, detail="User not found.")
    if (actor.role or "").strip().lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return actor


def _remove_local_file(path: str | None) -> None:
    if not path:
        return
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def _delete_document_bundle(db: Session, doc: Document) -> None:
    extracted_rows = db.query(ExtractedData).filter(ExtractedData.doc_id == doc.id).all()
    for row in extracted_rows:
        delete_extracted_record(row.id)
        db.delete(row)

    compliance_rows = db.query(ComplianceResult).filter(ComplianceResult.doc_id == doc.id).all()
    for row in compliance_rows:
        delete_compliance_record(row.id)
        db.delete(row)

    _remove_local_file(doc.file_path)
    if (doc.storage_provider or "").lower() == "firebase":
        delete_storage_blob(doc.storage_path)

    delete_doc_record(doc.id)
    db.delete(doc)


@router.get("/overview")
async def admin_overview(user_id: int, db: Session = Depends(get_db)):
    _require_admin(db, user_id)

    total_users = db.query(func.count(User.id)).scalar() or 0
    total_files = db.query(func.count(Document.id)).scalar() or 0
    total_cases = db.query(func.count(Case.id)).scalar() or 0
    total_admins = db.query(func.count(User.id)).filter(func.lower(User.role) == "admin").scalar() or 0

    return {
        "users": total_users,
        "admins": total_admins,
        "files": total_files,
        "cases": total_cases,
    }


@router.get("/users")
async def admin_list_users(user_id: int, db: Session = Depends(get_db)):
    _require_admin(db, user_id)

    users = db.query(User).order_by(User.id.asc()).all()
    case_counts = dict(
        db.query(Case.user_id, func.count(Case.id))
        .group_by(Case.user_id)
        .all()
    )
    file_counts = dict(
        db.query(Document.user_id, func.count(Document.id))
        .group_by(Document.user_id)
        .all()
    )

    return {
        "users": [
            {
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "cases_created": int(case_counts.get(user.id, 0) or 0),
                "files_uploaded": int(file_counts.get(user.id, 0) or 0),
            }
            for user in users
        ]
    }


@router.get("/files")
async def admin_list_files(
    user_id: int,
    page: int = 1,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    _require_admin(db, user_id)
    page = max(page, 1)
    limit = min(max(limit, 1), 200)

    base_query = db.query(Document)
    total = base_query.count()
    docs = (
        base_query
        .order_by(Document.upload_time.desc(), Document.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    user_map = {item.id: item for item in db.query(User).all()}
    case_map = {item.id: item for item in db.query(Case).all()}

    return {
        "files": [
            {
                "document_id": doc.id,
                "filename": doc.filename,
                "doc_type": doc.doc_type,
                "file_type": doc.file_type,
                "upload_time": doc.upload_time.isoformat(),
                "owner_user_id": doc.user_id,
                "owner_name": user_map.get(doc.user_id).name if user_map.get(doc.user_id) else None,
                "case_id": doc.case_id,
                "case_title": case_map.get(doc.case_id).title if case_map.get(doc.case_id) else None,
            }
            for doc in docs
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/cases")
async def admin_list_cases(
    user_id: int,
    page: int = 1,
    limit: int = 200,
    db: Session = Depends(get_db),
):
    _require_admin(db, user_id)
    page = max(page, 1)
    limit = min(max(limit, 1), 200)

    base_query = db.query(Case)
    total = base_query.count()
    cases = (
        base_query
        .order_by(Case.created_at.desc(), Case.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    case_ids = [item.id for item in cases]
    evidence_counts = {}
    if case_ids:
        evidence_counts = dict(
            db.query(Document.case_id, func.count(Document.id))
            .filter(Document.case_id.in_(case_ids))
            .group_by(Document.case_id)
            .all()
        )
    user_map = {item.id: item for item in db.query(User).all()}

    return {
        "cases": [
            {
                "case_id": item.id,
                "title": item.title,
                "description": item.description,
                "created_at": item.created_at.isoformat(),
                "owner_user_id": item.user_id,
                "owner_name": user_map.get(item.user_id).name if user_map.get(item.user_id) else None,
                "evidence_count": int(evidence_counts.get(item.id, 0) or 0),
            }
            for item in cases
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.delete("/files/{doc_id}")
async def admin_delete_file(doc_id: int, user_id: int, db: Session = Depends(get_db)):
    actor = _require_admin(db, user_id)
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="File not found.")

    filename = doc.filename
    _delete_document_bundle(db, doc)

    log = AuditLog(
        user_id=actor.id,
        action=f"Admin deleted file {filename} (doc_id={doc_id})",
        timestamp=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    sync_audit_record(log)

    return {
        "status": "success",
        "message": f"File {filename} deleted.",
        "document_id": doc_id,
    }


@router.delete("/cases/{case_id}")
async def admin_delete_case(case_id: int, user_id: int, db: Session = Depends(get_db)):
    actor = _require_admin(db, user_id)
    target_case = db.query(Case).filter(Case.id == case_id).first()
    if not target_case:
        raise HTTPException(status_code=404, detail="Case not found.")

    docs = db.query(Document).filter(Document.case_id == case_id).all()
    deleted_doc_count = 0
    for doc in docs:
        _delete_document_bundle(db, doc)
        deleted_doc_count += 1

    case_title = target_case.title
    delete_case_record(target_case.id)
    db.delete(target_case)

    log = AuditLog(
        user_id=actor.id,
        action=f"Admin deleted case {case_title} (case_id={case_id}) with {deleted_doc_count} files",
        timestamp=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    sync_audit_record(log)

    return {
        "status": "success",
        "message": f"Case {case_title} deleted.",
        "case_id": case_id,
        "deleted_files": deleted_doc_count,
    }


@router.delete("/users/{target_user_id}")
async def admin_delete_user(target_user_id: int, user_id: int, db: Session = Depends(get_db)):
    actor = _require_admin(db, user_id)
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")
    if actor.id == target_user.id:
        raise HTTPException(status_code=400, detail="Admin cannot delete their own account.")

    if (target_user.role or "").strip().lower() == "admin":
        admin_count = db.query(func.count(User.id)).filter(func.lower(User.role) == "admin").scalar() or 0
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last admin account.")

    target_case_ids = [row[0] for row in db.query(Case.id).filter(Case.user_id == target_user_id).all()]
    docs_query = db.query(Document).filter(Document.user_id == target_user_id)
    if target_case_ids:
        docs_query = db.query(Document).filter(
            or_(Document.user_id == target_user_id, Document.case_id.in_(target_case_ids))
        )

    docs_to_delete = {doc.id: doc for doc in docs_query.all()}
    for doc in docs_to_delete.values():
        _delete_document_bundle(db, doc)

    owned_cases = db.query(Case).filter(Case.user_id == target_user_id).all()
    for owned_case in owned_cases:
        delete_case_record(owned_case.id)
        db.delete(owned_case)

    target_logs = db.query(AuditLog).filter(AuditLog.user_id == target_user_id).all()
    for log in target_logs:
        delete_audit_record(log.id)
        db.delete(log)

    delete_user_record(target_user.id)
    target_email = target_user.email
    db.delete(target_user)

    audit = AuditLog(
        user_id=actor.id,
        action=f"Admin deleted user {target_email} (user_id={target_user_id})",
        timestamp=datetime.utcnow(),
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    sync_audit_record(audit)

    return {
        "status": "success",
        "message": f"User {target_email} deleted.",
        "deleted_files": len(docs_to_delete),
        "deleted_cases": len(owned_cases),
    }
