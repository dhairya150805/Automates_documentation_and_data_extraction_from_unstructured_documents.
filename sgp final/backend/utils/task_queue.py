import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, asdict
import uuid
from sqlalchemy.orm import Session
from database.db import get_db

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class Task:
    id: str
    name: str
    function_name: str
    args: List[Any]
    kwargs: Dict[str, Any]
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    scheduled_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

class TaskQueue:
    """Advanced async task queue with retry logic"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.pending_tasks: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_functions: Dict[str, Callable] = {}
        self.workers: List[asyncio.Task] = []
        self.max_workers = 5
        
    def register_task_function(self, name: str, func: Callable):
        """Register a function that can be called by tasks"""
        self.task_functions[name] = func
    
    async def add_task(
        self,
        function_name: str,
        args: List[Any] = None,
        kwargs: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        delay: timedelta = None,
        max_retries: int = 3
    ) -> str:
        """Add a task to the queue"""
        task_id = str(uuid.uuid4())
        scheduled_at = datetime.utcnow() + (delay or timedelta())
        
        task = Task(
            id=task_id,
            name=function_name,
            function_name=function_name,
            args=args or [],
            kwargs=kwargs or {},
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow(),
            scheduled_at=scheduled_at,
            max_retries=max_retries
        )
        
        self.tasks[task_id] = task
        
        # Add to priority queue (lower priority value = higher priority)
        await self.pending_tasks.put((-priority.value, scheduled_at, task_id))
        
        return task_id
    
    async def start_workers(self):
        """Start background worker tasks"""
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
    
    async def _worker(self, worker_name: str):
        """Worker coroutine that processes tasks"""
        while True:
            try:
                # Get next task
                _, scheduled_at, task_id = await self.pending_tasks.get()
                
                if task_id not in self.tasks:
                    continue
                    
                task = self.tasks[task_id]
                
                # Check if task is scheduled for future
                if scheduled_at > datetime.utcnow():
                    await asyncio.sleep((scheduled_at - datetime.utcnow()).total_seconds())
                
                # Execute task
                await self._execute_task(task, worker_name)
                
                # Mark task as done
                self.pending_tasks.task_done()
                
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(1)
    
    async def _execute_task(self, task: Task, worker_name: str):
        """Execute a single task"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        
        try:
            # Get the function to execute
            if task.function_name not in self.task_functions:
                raise ValueError(f"Unknown task function: {task.function_name}")
            
            func = self.task_functions[task.function_name]
            
            # Execute the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*task.args, **task.kwargs)
            else:
                result = func(*task.args, **task.kwargs)
            
            # Task completed successfully
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = result
            
        except Exception as e:
            # Task failed
            task.error = str(e)
            
            if task.retry_count < task.max_retries:
                # Retry the task
                task.status = TaskStatus.RETRYING
                task.retry_count += 1
                
                # Add back to queue with delay
                retry_delay = timedelta(seconds=min(60 * (2 ** task.retry_count), 3600))
                scheduled_at = datetime.utcnow() + retry_delay
                
                await self.pending_tasks.put(
                    (-task.priority.value, scheduled_at, task.id)
                )
            else:
                # Max retries reached
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
    
    def get_task_status(self, task_id: str) -> Optional[Task]:
        """Get task status"""
        return self.tasks.get(task_id)
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = sum(
                1 for task in self.tasks.values() 
                if task.status == status
            )
        
        return {
            "total_tasks": len(self.tasks),
            "status_counts": status_counts,
            "pending_queue_size": self.pending_tasks.qsize(),
            "running_tasks": len(self.running_tasks),
            "active_workers": len([w for w in self.workers if not w.done()])
        }

# Global task queue instance
task_queue = TaskQueue()

# Task function decorators
def background_task(
    name: str = None,
    priority: TaskPriority = TaskPriority.NORMAL,
    max_retries: int = 3
):
    """Decorator to register a function as a background task"""
    def decorator(func):
        task_name = name or func.__name__
        task_queue.register_task_function(task_name, func)
        
        async def enqueue(*args, delay: timedelta = None, **kwargs):
            return await task_queue.add_task(
                function_name=task_name,
                args=list(args),
                kwargs=kwargs,
                priority=priority,
                delay=delay,
                max_retries=max_retries
            )
        
        func.enqueue = enqueue
        return func
    
    return decorator

# Example background tasks
@background_task("process_document", priority=TaskPriority.HIGH)
async def process_document_task(document_id: int, user_id: int):
    """Background task for document processing"""
    try:
        from ai.ocr import perform_ocr
        from ai.layoutlm import extract_key_values
        from ai.summarizer import summarize_text
        
        # Get document from database
        with next(get_db()) as db:
            from database.models import Document
            doc = db.query(Document).filter(Document.id == document_id).first()
            
            if not doc:
                raise ValueError(f"Document {document_id} not found")
            
            # Perform OCR
            ocr_result = perform_ocr(doc.file_path)
            doc.ocr_text = ocr_result.get("text", "")
            
            # Extract key-value pairs
            extracted = extract_key_values(doc.file_path, doc.ocr_text)
            
            # Generate summary
            doc.summary = summarize_text(doc.ocr_text)
            
            db.commit()
            
            return {
                "document_id": document_id,
                "ocr_text_length": len(doc.ocr_text),
                "extracted_fields": len(extracted),
                "summary_length": len(doc.summary or "")
            }
            
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Document processing failed: {e}")
        raise

@background_task("cleanup_old_files", priority=TaskPriority.LOW)
async def cleanup_old_files_task(days_old: int = 30):
    """Background task for cleaning up old files"""
    import os
    from pathlib import Path
    
    storage_path = Path("backend/storage")
    cutoff_date = datetime.now() - timedelta(days=days_old)
    
    cleaned_files = 0
    for file_path in storage_path.glob("*"):
        if file_path.is_file():
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_time < cutoff_date:
                try:
                    os.remove(file_path)
                    cleaned_files += 1
                except Exception:
                    pass
    
    return {"cleaned_files": cleaned_files}
