import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from database.models import Base

BACKEND_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SQLITE_PATH = BACKEND_ROOT / "local.db"


def _build_database_url() -> str:
    configured = os.getenv("DATABASE_URL")
    if configured:
        return configured
    return f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"


def _ensure_sqlite_directory(database_url: str) -> None:
    if not database_url.startswith("sqlite:///"):
        return
    sqlite_target = database_url.replace("sqlite:///", "", 1)
    if not sqlite_target or sqlite_target == ":memory:":
        return
    sqlite_path = Path(sqlite_target).expanduser().resolve()
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)


DATABASE_URL = _build_database_url()
DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").strip().lower() == "true"
_ensure_sqlite_directory(DATABASE_URL)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
    echo=DATABASE_ECHO,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)
    _ensure_user_auth_columns()
    _ensure_case_owner_column()
    _ensure_document_case_columns()
    _ensure_document_storage_columns()
    _backfill_case_owner_from_documents()


def _sqlite_columns(table_name: str):
    with engine.connect() as conn:
        result = conn.execute(text(f"PRAGMA table_info({table_name})"))
        return {row[1] for row in result.fetchall()}


def _ensure_user_auth_columns():
    if engine.dialect.name != "sqlite":
        return
    existing = _sqlite_columns("users")
    with engine.begin() as conn:
        if "password_hash" not in existing:
            conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR"))
        if "password_salt" not in existing:
            conn.execute(text("ALTER TABLE users ADD COLUMN password_salt VARCHAR"))


def _ensure_document_case_columns():
    if engine.dialect.name != "sqlite":
        return
    existing = _sqlite_columns("documents")
    with engine.begin() as conn:
        if "case_id" not in existing:
            conn.execute(text("ALTER TABLE documents ADD COLUMN case_id INTEGER"))
        if "file_type" not in existing:
            conn.execute(text("ALTER TABLE documents ADD COLUMN file_type VARCHAR"))


def _ensure_document_storage_columns():
    if engine.dialect.name != "sqlite":
        return
    existing = _sqlite_columns("documents")
    with engine.begin() as conn:
        if "storage_provider" not in existing:
            conn.execute(text("ALTER TABLE documents ADD COLUMN storage_provider VARCHAR"))
        if "storage_path" not in existing:
            conn.execute(text("ALTER TABLE documents ADD COLUMN storage_path VARCHAR"))
        if "storage_url" not in existing:
            conn.execute(text("ALTER TABLE documents ADD COLUMN storage_url VARCHAR"))


def _ensure_case_owner_column():
    if engine.dialect.name != "sqlite":
        return
    existing = _sqlite_columns("cases")
    with engine.begin() as conn:
        if "user_id" not in existing:
            conn.execute(text("ALTER TABLE cases ADD COLUMN user_id INTEGER"))


def _backfill_case_owner_from_documents():
    if engine.dialect.name != "sqlite":
        return
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE cases
                SET user_id = (
                    SELECT d.user_id
                    FROM documents d
                    WHERE d.case_id = cases.id AND d.user_id IS NOT NULL
                    ORDER BY d.id ASC
                    LIMIT 1
                )
                WHERE user_id IS NULL
                """
            )
        )


def _masked_database_url(url: str) -> str:
    if "://" not in url or "@" not in url:
        return url
    scheme, remainder = url.split("://", 1)
    if "@" not in remainder:
        return url
    credentials, host = remainder.split("@", 1)
    if ":" in credentials:
        username = credentials.split(":", 1)[0]
        redacted_credentials = f"{username}:***"
    else:
        redacted_credentials = "***"
    return f"{scheme}://{redacted_credentials}@{host}"


def get_database_info():
    info = {
        "dialect": engine.dialect.name,
        "url": _masked_database_url(DATABASE_URL),
    }
    if engine.dialect.name == "sqlite":
        info["default_path"] = str(DEFAULT_SQLITE_PATH)
    return info


def restore_remote_data_if_configured():
    if os.getenv("FIREBASE_RESTORE_ON_STARTUP", "true").strip().lower() not in {"1", "true", "yes", "on"}:
        return None
    try:
        from utils.firebase_service import firebase_enabled, restore_firestore_to_sqlite
        if not firebase_enabled():
            return None
        db = SessionLocal()
        try:
            return restore_firestore_to_sqlite(db)
        finally:
            db.close()
    except Exception:
        return None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
