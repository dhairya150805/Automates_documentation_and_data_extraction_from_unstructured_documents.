# Demo Workflow - AI Case Documentation System

## Quick Demo Steps

### 1. Start the System
```powershell
# Terminal 1 - Backend
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend  
cd frontend; npm start

# Open: http://localhost:3000
```

### 2. Create a Case
1. Go to **Cases** page
2. Enter case title: "Patient 1001 - Medical Review"
3. Description: "Complete medical history and diagnostic review"
4. Click **Create Case** → Note the Case ID

### 3. Upload Evidence Documents
1. Go to **Upload** page
2. Set Case ID to the one from step 2
3. Upload multiple files:
   - Medical reports (PDF)
   - X-ray images (PNG/JPG)
   - Doctor's notes (DOCX)
   - Audio recordings (MP3/WAV)

### 4. Process the Case
1. Go back to **Cases** page
2. Find your case in "Case Pipeline" section
3. Check "Run compliance checks" (optional)
4. Click **Process Case**
   - This runs OCR on all documents
   - Extracts structured fields (names, dates, amounts)
   - Generates summaries
   - Validates compliance rules

### 5. Review & Correct Data
1. Go to **Review** page
2. Enter your Case ID
3. Click **Load Case**
4. Review extracted fields for each document
5. Correct any wrong values manually
6. Click **Save** for each document

### 6. Generate Final Report
1. Go back to **Cases** page
2. Enter Case ID in "Structured Case Summary"
3. Click **Load Summary** to see JSON output
4. Click **Download CSV** or **Download PDF** for final report

## Expected Output

The system will produce a structured case report containing:

```json
{
  "case": {
    "case_id": 1,
    "title": "Patient 1001 - Medical Review", 
    "description": "Complete medical history and diagnostic review",
    "created_at": "2026-02-10T14:30:00"
  },
  "evidence_count": 4,
  "evidence": [
    {
      "doc_id": 1,
      "filename": "medical_report.pdf",
      "file_type": "pdf",
      "doc_type": "medical_record",
      "extracted_data": [
        {"field": "Patient Name", "value": "John Doe", "confidence": 0.95},
        {"field": "Date of Birth", "value": "1985-03-15", "confidence": 0.92},
        {"field": "Diagnosis", "value": "Hypertension", "confidence": 0.88}
      ],
      "compliance": {
        "status": "PASS",
        "remarks": "All required fields present"
      }
    }
  ],
  "aggregated_fields": {
    "Patient Name": {
      "best": {"value": "John Doe", "confidence": 0.95, "doc_id": 1},
      "all": [{"value": "John Doe", "confidence": 0.95, "doc_id": 1}]
    }
  }
}
```

## Use Cases Demonstrated

- **Hospital**: Patient records + X-rays + audio notes → Medical case summary
- **Legal**: Court documents + evidence photos + witness recordings → Legal brief  
- **School**: Transcripts + applications + interview audio → Student profile
- **Pharma**: Research papers + trial data + compliance docs → Regulatory report

This demonstrates a complete **multi-modal, AI-powered case documentation system** suitable for any industry requiring structured data extraction from unstructured evidence.
