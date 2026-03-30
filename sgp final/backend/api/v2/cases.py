from fastapi import APIRouter, Depends, HTTPException
from utils.advanced_auth import get_current_user, require_admin
from models.request_models import CaseCreateRequest, CaseResponse
from utils.performance_monitoring import monitor_performance
from utils.task_queue import process_document_task
from sqlalchemy.orm import Session
from database.db import get_db

# API Version 2 - Enhanced functionality
router = APIRouter(prefix="/v2")

@router.post("/cases/", response_model=CaseResponse)
@monitor_performance("create_case_v2")
async def create_case_v2(
    case_data: CaseCreateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a new case with enhanced validation and user tracking
    
    - **Enhanced validation**: Comprehensive input validation
    - **User tracking**: Links cases to authenticated users  
    - **Performance monitoring**: Tracks operation performance
    - **Audit logging**: Complete audit trail
    """
    from database.models import Case, AuditLog
    from datetime import datetime
    
    # Create case with user association
    case = Case(
        title=case_data.title,
        description=case_data.description,
        created_at=datetime.utcnow(),
        user_id=current_user.id  # Associate with current user
    )
    
    db.add(case)
    db.commit()
    db.refresh(case)
    
    # Add audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action=f"Created case: {case.title}",
        timestamp=datetime.utcnow(),
        details=f"Case ID: {case.id}"
    )
    db.add(audit_log)
    db.commit()
    
    return CaseResponse(
        case_id=case.id,
        title=case.title,
        description=case.description,
        created_at=case.created_at,
        evidence_count=0
    )

@router.post("/cases/{case_id}/process-async")
@monitor_performance("process_case_async")
async def process_case_async_v2(
    case_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Process all documents in a case asynchronously using background tasks
    
    - **Background processing**: Non-blocking operation
    - **Progress tracking**: Real-time status updates
    - **Task management**: Queued with priority handling
    """
    from database.models import Case, Document
    
    # Verify case exists and user has access
    case = db.query(Case).filter(
        Case.id == case_id,
        Case.user_id == current_user.id
    ).first()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or access denied")
    
    # Get all documents in the case
    documents = db.query(Document).filter(Document.case_id == case_id).all()
    
    if not documents:
        raise HTTPException(status_code=400, detail="No documents found in case")
    
    # Queue background tasks for each document
    task_ids = []
    for doc in documents:
        task_id = await process_document_task.enqueue(doc.id, current_user.id)
        task_ids.append(task_id)
    
    return {
        "status": "processing",
        "case_id": case_id,
        "document_count": len(documents),
        "task_ids": task_ids,
        "message": "Documents are being processed in the background"
    }

@router.get("/admin/metrics")
@monitor_performance("get_metrics")
async def get_system_metrics_v2(
    current_user = Depends(require_admin)
):
    """
    Get comprehensive system metrics (Admin only)
    
    - **Performance metrics**: Response times, throughput
    - **System health**: CPU, memory, disk usage
    - **Task queue stats**: Pending/completed tasks
    """
    from utils.performance_monitoring import metrics
    from utils.task_queue import task_queue
    
    return {
        "performance": {
            "case_creation": metrics.get_metric_summary("operation_duration_create_case_v2"),
            "document_processing": metrics.get_metric_summary("operation_duration_process_document"),
        },
        "system": metrics.get_system_metrics(),
        "task_queue": task_queue.get_queue_stats(),
        "timestamp": datetime.utcnow()
    }
