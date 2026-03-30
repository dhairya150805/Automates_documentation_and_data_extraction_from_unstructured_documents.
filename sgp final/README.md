# AI-Based Intelligent Case Documentation and Compliance Automation System

## Overview
This project is a full-stack, final-year level system that accepts **multi-format evidence for a case** (PDFs, images, DOCX, audio), extracts structured data using **pre-trained AI models**, validates compliance via **rule-based logic**, and generates summaries, reports, and audit logs. **No model is trained from scratch.**

## Stack
- Frontend: React, Axios
- Backend: FastAPI, Python
- Database: SQLite/PostgreSQL + optional Firebase Firestore (cloud persistence)
- File Storage: Local storage + optional Firebase Storage (cloud persistence)
- AI/NLP: Tesseract OCR, HuggingFace Transformers (LayoutLMv3, BART, zero-shot BERT)

## Setup
1. Create and activate Python venv
2. Install backend dependencies:
   - fastapi, uvicorn, sqlalchemy, psycopg, firebase-admin, pytesseract, opencv-python, pillow, transformers, torch
   - pdf2image (PDF OCR), python-docx (DOCX parsing), reportlab (PDF reports), openai-whisper (audio)
   - Note: pdf2image requires Poppler installed on your OS.
3. Start backend:
   - `uvicorn backend.main:app --reload`
4. Frontend:
   - `npm install`
   - `npm start`

## Database Configuration
- Default: if `DATABASE_URL` is not set, backend uses SQLite at `backend/local.db`.
- PostgreSQL example:
  - `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/sgp`
- Optional SQL debug logging:
  - `DATABASE_ECHO=true`
- See `backend/.env.example` for template values.

## Firebase Persistence (Recommended)
- Configure in `backend/.env.example`:
  - `FIREBASE_SERVICE_ACCOUNT_JSON`
  - `FIREBASE_PROJECT_ID`
  - `FIREBASE_STORAGE_BUCKET`
- Behavior when enabled:
  - Uploaded files are copied to Firebase Storage.
  - Users/cases/documents/logs/extracted/compliance metadata are synced to Firestore.
  - On backend startup, Firestore data is restored into local DB (`FIREBASE_RESTORE_ON_STARTUP=true`).

## Local Requirements
- Tesseract OCR must be installed and available on PATH.
- For PDFs, Poppler is required by `pdf2image`.
- For audio transcription, `openai-whisper` + FFmpeg are required.

## API Endpoints
- `POST /cases` — create a case
- `GET /cases` — list cases
- `GET /cases/{case_id}` — case details
- `GET /cases/{case_id}/summary` — structured case summary
- `POST /upload` — file upload
- `POST /ocr` — OCR extraction
- `POST /classify` — optional zero-shot classification
- `POST /extract` — key-value extraction
- `POST /compliance` — rule-based compliance check
- `POST /summary` — summarization
- `POST /auth/register` — demo user registration
- `POST /auth/login` — demo user login (email + password)
- `GET /logs` — audit logs
- `GET /reports` — report download (csv/pdf)
- `GET /stats` — dashboard stats

## Example JSON Responses
### OCR
```
{
  "status": "success",
  "doc_id": 1,
  "text": "Invoice No 12345 Date 01/01/2026",
  "boxes": [{"text": "Invoice", "left": 10, "top": 20, "width": 50, "height": 15}]
}
```

### Extraction
```
{
  "status": "success",
  "doc_id": 1,
  "extracted_data": [
    {"field": "Invoice No", "value": "12345", "confidence": 0.65},
    {"field": "Amount", "value": "1500.00", "confidence": 0.65}
  ]
}
```

### Compliance
```
{
  "status": "success",
  "doc_id": 1,
  "compliance": {
    "status": "PASS",
    "remarks": "All checks passed"
  }
}
```

## Notes
- LayoutLMv3 is loaded as a **pre-trained model**. For local demo, the extraction step includes a heuristic fallback.
- Summarization uses BART (pre-trained).
- Classification uses zero-shot BART-MNLI (pre-trained).
- No model training or fine-tuning is required.
