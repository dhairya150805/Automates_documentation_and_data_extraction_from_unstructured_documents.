from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)
    password_hash = Column(String, nullable=True)
    password_salt = Column(String, nullable=True)

    documents = relationship("Document", back_populates="user")
    cases = relationship("Case", back_populates="user")

class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="cases")
    documents = relationship("Document", back_populates="case")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    upload_time = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    doc_type = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    file_path = Column(String, nullable=False)
    storage_provider = Column(String, nullable=True)
    storage_path = Column(String, nullable=True)
    storage_url = Column(String, nullable=True)
    ocr_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)

    user = relationship("User", back_populates="documents")
    case = relationship("Case", back_populates="documents")

class ExtractedData(Base):
    __tablename__ = "extracted_data"
    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(Integer, ForeignKey("documents.id"))
    field = Column(String, nullable=False)
    value = Column(String, nullable=True)
    confidence = Column(Float, nullable=False)

class ComplianceResult(Base):
    __tablename__ = "compliance_results"
    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(Integer, ForeignKey("documents.id"))
    status = Column(String, nullable=False)
    remarks = Column(Text, nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
