from collections import defaultdict


def build_case_summary(case, documents, extracted_lookup, compliance_lookup):
    evidence = []
    aggregated = defaultdict(list)

    for doc in documents:
        extracted = extracted_lookup.get(doc.id, [])
        compliance = compliance_lookup.get(doc.id)
        evidence.append({
            "doc_id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "doc_type": doc.doc_type,
            "upload_time": doc.upload_time.isoformat(),
            "summary": doc.summary,
            "text_preview": (doc.ocr_text or "")[:500],
            "compliance": (
                {
                    "status": compliance.status,
                    "remarks": compliance.remarks,
                }
                if compliance else None
            ),
            "extracted_data": [
                {
                    "field": item.field,
                    "value": item.value,
                    "confidence": item.confidence,
                }
                for item in extracted
            ],
        })

        for item in extracted:
            aggregated[item.field].append({
                "value": item.value,
                "confidence": item.confidence,
                "doc_id": doc.id,
            })

    aggregated_fields = {}
    for field, values in aggregated.items():
        best = max(values, key=lambda x: x.get("confidence") or 0)
        aggregated_fields[field] = {
            "best": best,
            "all": values,
        }

    return {
        "case": {
            "case_id": case.id,
            "title": case.title,
            "description": case.description,
            "created_at": case.created_at.isoformat(),
        },
        "evidence_count": len(documents),
        "evidence": evidence,
        "aggregated_fields": aggregated_fields,
    }
