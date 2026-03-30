import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import firebase_admin
    from firebase_admin import credentials, firestore, storage
except Exception:  # pragma: no cover - optional dependency
    firebase_admin = None
    credentials = None
    firestore = None
    storage = None


_FIREBASE_APP = None
_FIREBASE_ERROR: Optional[str] = None


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _to_iso(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _from_iso(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def initialize_firebase() -> bool:
    global _FIREBASE_APP, _FIREBASE_ERROR
    if _FIREBASE_APP is not None:
        return True
    if firebase_admin is None:
        _FIREBASE_ERROR = "firebase_admin is not installed."
        return False

    credential_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    credential_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON_CONTENT", "").strip()
    storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET", "").strip()
    project_id = os.getenv("FIREBASE_PROJECT_ID", "").strip()

    if not credential_path and not credential_json:
        _FIREBASE_ERROR = "Firebase credentials are not configured."
        return False

    try:
        if credential_path:
            cred = credentials.Certificate(credential_path)
        else:
            cred_data = json.loads(credential_json)
            cred = credentials.Certificate(cred_data)

        options: Dict[str, str] = {}
        if storage_bucket:
            options["storageBucket"] = storage_bucket
        if project_id:
            options["projectId"] = project_id

        _FIREBASE_APP = firebase_admin.initialize_app(cred, options=options or None)
        _FIREBASE_ERROR = None
        return True
    except Exception as exc:
        _FIREBASE_ERROR = f"{type(exc).__name__}: {exc}"
        return False


def firebase_enabled() -> bool:
    return initialize_firebase()


def get_firebase_status() -> Dict[str, Any]:
    enabled = firebase_enabled()
    return {
        "enabled": enabled,
        "error": None if enabled else _FIREBASE_ERROR,
        "storage_bucket": os.getenv("FIREBASE_STORAGE_BUCKET", "").strip() or None,
    }


def _firestore_client():
    if not firebase_enabled():
        return None
    return firestore.client()


def _storage_bucket():
    if not firebase_enabled():
        return None
    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET", "").strip()
    if not bucket_name:
        return None
    return storage.bucket()


def upload_bytes(blob_path: str, data: bytes, content_type: Optional[str] = None) -> Optional[Dict[str, str]]:
    bucket = _storage_bucket()
    if bucket is None:
        return None

    blob = bucket.blob(blob_path)
    blob.upload_from_string(data, content_type=content_type)
    if _env_bool("FIREBASE_STORAGE_MAKE_PUBLIC", "false"):
        try:
            blob.make_public()
        except Exception:
            pass

    return {
        "storage_path": blob_path,
        "storage_url": blob.public_url,
    }


def download_to_file(blob_path: str, local_path: str) -> bool:
    bucket = _storage_bucket()
    if bucket is None:
        return False
    blob = bucket.blob(blob_path)
    local_target = Path(local_path)
    local_target.parent.mkdir(parents=True, exist_ok=True)
    blob.download_to_filename(str(local_target))
    return True


def delete_storage_blob(blob_path: Optional[str]) -> bool:
    if not blob_path:
        return False
    bucket = _storage_bucket()
    if bucket is None:
        return False
    try:
        blob = bucket.blob(blob_path)
        if blob.exists():
            blob.delete()
        return True
    except Exception:
        return False


def sync_document(collection: str, record_id: int, payload: Dict[str, Any]) -> None:
    client = _firestore_client()
    if client is None:
        return
    data = {k: _to_iso(v) for k, v in payload.items()}
    data["id"] = int(record_id)
    data["updated_at"] = datetime.utcnow().isoformat()
    client.collection(collection).document(str(record_id)).set(data, merge=True)


def delete_document(collection: str, record_id: int) -> None:
    client = _firestore_client()
    if client is None:
        return
    try:
        client.collection(collection).document(str(record_id)).delete()
    except Exception:
        pass


def sync_user_record(user) -> None:
    sync_document(
        "users",
        user.id,
        {
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "password_hash": user.password_hash,
            "password_salt": user.password_salt,
        },
    )


def delete_user_record(user_id: int) -> None:
    delete_document("users", user_id)


def sync_case_record(case) -> None:
    sync_document(
        "cases",
        case.id,
        {
            "user_id": case.user_id,
            "title": case.title,
            "description": case.description,
            "created_at": case.created_at,
        },
    )


def delete_case_record(case_id: int) -> None:
    delete_document("cases", case_id)


def sync_doc_record(doc) -> None:
    sync_document(
        "documents",
        doc.id,
        {
            "filename": doc.filename,
            "upload_time": doc.upload_time,
            "user_id": doc.user_id,
            "case_id": doc.case_id,
            "doc_type": doc.doc_type,
            "file_type": doc.file_type,
            "file_path": doc.file_path,
            "ocr_text": doc.ocr_text,
            "summary": doc.summary,
            "storage_provider": getattr(doc, "storage_provider", None),
            "storage_path": getattr(doc, "storage_path", None),
            "storage_url": getattr(doc, "storage_url", None),
        },
    )


def delete_doc_record(doc_id: int) -> None:
    delete_document("documents", doc_id)


def sync_audit_record(log) -> None:
    sync_document(
        "audit_logs",
        log.id,
        {
            "user_id": log.user_id,
            "action": log.action,
            "timestamp": log.timestamp,
        },
    )


def delete_audit_record(log_id: int) -> None:
    delete_document("audit_logs", log_id)


def sync_extracted_record(item) -> None:
    sync_document(
        "extracted_data",
        item.id,
        {
            "doc_id": item.doc_id,
            "field": item.field,
            "value": item.value,
            "confidence": item.confidence,
        },
    )


def delete_extracted_record(item_id: int) -> None:
    delete_document("extracted_data", item_id)


def sync_compliance_record(item) -> None:
    sync_document(
        "compliance_results",
        item.id,
        {
            "doc_id": item.doc_id,
            "status": item.status,
            "remarks": item.remarks,
        },
    )


def delete_compliance_record(item_id: int) -> None:
    delete_document("compliance_results", item_id)


def restore_firestore_to_sqlite(db) -> Dict[str, int]:
    client = _firestore_client()
    if client is None:
        return {"users": 0, "cases": 0, "documents": 0, "audit_logs": 0, "extracted_data": 0, "compliance_results": 0}

    from database.models import User, Case, Document, AuditLog, ExtractedData, ComplianceResult

    counts = {"users": 0, "cases": 0, "documents": 0, "audit_logs": 0, "extracted_data": 0, "compliance_results": 0}

    for snap in client.collection("users").stream():
        data = snap.to_dict() or {}
        item = User(
            id=int(snap.id),
            name=data.get("name") or "",
            email=(data.get("email") or "").lower(),
            role=data.get("role") or "User",
            password_hash=data.get("password_hash"),
            password_salt=data.get("password_salt"),
        )
        db.merge(item)
        counts["users"] += 1

    for snap in client.collection("cases").stream():
        data = snap.to_dict() or {}
        created_at = _from_iso(data.get("created_at")) or datetime.utcnow()
        item = Case(
            id=int(snap.id),
            user_id=data.get("user_id"),
            title=data.get("title") or "Untitled Case",
            description=data.get("description"),
            created_at=created_at,
        )
        db.merge(item)
        counts["cases"] += 1

    for snap in client.collection("documents").stream():
        data = snap.to_dict() or {}
        upload_time = _from_iso(data.get("upload_time")) or datetime.utcnow()
        item = Document(
            id=int(snap.id),
            filename=data.get("filename") or f"doc_{snap.id}",
            upload_time=upload_time,
            user_id=data.get("user_id"),
            case_id=data.get("case_id"),
            doc_type=data.get("doc_type") or "Other",
            file_type=data.get("file_type"),
            file_path=data.get("file_path") or "",
            ocr_text=data.get("ocr_text"),
            summary=data.get("summary"),
            storage_provider=data.get("storage_provider"),
            storage_path=data.get("storage_path"),
            storage_url=data.get("storage_url"),
        )
        db.merge(item)
        counts["documents"] += 1

    for snap in client.collection("audit_logs").stream():
        data = snap.to_dict() or {}
        ts = _from_iso(data.get("timestamp")) or datetime.utcnow()
        item = AuditLog(
            id=int(snap.id),
            user_id=data.get("user_id") or 0,
            action=data.get("action") or "",
            timestamp=ts,
        )
        db.merge(item)
        counts["audit_logs"] += 1

    for snap in client.collection("extracted_data").stream():
        data = snap.to_dict() or {}
        item = ExtractedData(
            id=int(snap.id),
            doc_id=data.get("doc_id"),
            field=data.get("field") or "",
            value=data.get("value"),
            confidence=float(data.get("confidence") or 0),
        )
        db.merge(item)
        counts["extracted_data"] += 1

    for snap in client.collection("compliance_results").stream():
        data = snap.to_dict() or {}
        item = ComplianceResult(
            id=int(snap.id),
            doc_id=data.get("doc_id"),
            status=data.get("status") or "WARNING",
            remarks=data.get("remarks"),
        )
        db.merge(item)
        counts["compliance_results"] += 1

    db.commit()
    return counts
