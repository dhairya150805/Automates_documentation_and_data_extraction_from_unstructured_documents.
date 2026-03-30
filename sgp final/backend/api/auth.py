import os
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import User, AuditLog
from utils.auth import hash_password, verify_password
from utils.firebase_service import sync_user_record, sync_audit_record
from datetime import datetime

router = APIRouter()
ADMIN_REGISTRATION_KEY = os.getenv("ADMIN_REGISTRATION_KEY", "charusatsgp").strip()


def _normalize_role(value: str | None) -> str:
    role = (value or "User").strip().lower()
    if role == "admin":
        return "Admin"
    return "User"


@router.post("/register")
async def register(payload: dict, db: Session = Depends(get_db)):
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    role = _normalize_role(payload.get("role"))
    password = (payload.get("password") or "").strip()
    admin_key = (payload.get("admin_key") or "").strip()

    if not name or not email or not password:
        raise HTTPException(status_code=400, detail="Name, email, and password are required.")
    if role == "Admin" and admin_key != ADMIN_REGISTRATION_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key. Admin account cannot be created.")

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        if existing.password_hash:
            raise HTTPException(status_code=409, detail="Account already exists. Please login.")
        pwd_hash, pwd_salt = hash_password(password)
        existing.password_hash = pwd_hash
        existing.password_salt = pwd_salt
        existing.role = role
        db.commit()
        db.refresh(existing)
        sync_user_record(existing)
        return {
            "status": "updated",
            "user_id": existing.id,
            "name": existing.name,
            "email": existing.email,
            "role": existing.role,
        }

    pwd_hash, pwd_salt = hash_password(password)
    user = User(name=name, email=email, role=role)
    user.password_hash = pwd_hash
    user.password_salt = pwd_salt
    db.add(user)
    db.commit()
    db.refresh(user)
    sync_user_record(user)

    log = AuditLog(user_id=user.id, action=f"User registered: {user.email}", timestamp=datetime.utcnow())
    db.add(log)
    db.commit()
    db.refresh(log)
    sync_audit_record(log)

    return {
        "status": "created",
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
    }


@router.post("/login")
async def login(payload: dict, db: Session = Depends(get_db)):
    email = (payload.get("email") or "").strip().lower()
    password = (payload.get("password") or "").strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required.")
    if not password:
        raise HTTPException(status_code=400, detail="Password is required.")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please register first.")
    if not verify_password(password, user.password_hash, user.password_salt):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    log = AuditLog(user_id=user.id, action=f"User login: {user.email}", timestamp=datetime.utcnow())
    db.add(log)
    db.commit()
    db.refresh(log)
    sync_audit_record(log)

    return {
        "status": "success",
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
    }
