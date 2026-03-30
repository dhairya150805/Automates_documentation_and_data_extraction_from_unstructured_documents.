import logging
import json
from datetime import datetime
from typing import Any, Dict
from contextvars import ContextVar
from fastapi import Request, Response
import time

# Context variable for request tracking
request_id_context: ContextVar[str] = ContextVar('request_id', default='')

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add request ID if available
        request_id = request_id_context.get('')
        if request_id:
            log_entry['request_id'] = request_id
        
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_entry['data'] = record.extra_data
            
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry)

def setup_logging():
    """Setup advanced logging configuration"""
    
    # Create formatters
    json_formatter = JSONFormatter()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup file handler for JSON logs
    file_handler = logging.FileHandler('logs/application.json.log')
    file_handler.setFormatter(json_formatter)
    file_handler.setLevel(logging.INFO)
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.DEBUG)
    
    # Setup error file handler
    error_handler = logging.FileHandler('logs/errors.log')
    error_handler.setFormatter(json_formatter)
    error_handler.setLevel(logging.ERROR)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(error_handler)
    
    # Configure specific loggers
    logging.getLogger('uvicorn.access').handlers = []  # Remove default uvicorn handler
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    return root_logger

class RequestLoggingMiddleware:
    """Middleware for request/response logging"""
    
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger(__name__)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Generate request ID
        import uuid
        request_id = str(uuid.uuid4())[:8]
        request_id_context.set(request_id)
        
        start_time = time.time()
        
        # Log request
        self.logger.info(
            "Request started",
            extra={
                'extra_data': {
                    'request_id': request_id,
                    'method': request.method,
                    'url': str(request.url),
                    'client_ip': request.client.host,
                    'user_agent': request.headers.get('user-agent', ''),
                }
            }
        )
        
        response_body = b""
        response_status = 500
        
        async def send_wrapper(message):
            nonlocal response_body, response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
            elif message["type"] == "http.response.body":
                response_body += message.get("body", b"")
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            self.logger.error(
                f"Request failed: {str(e)}",
                exc_info=True,
                extra={
                    'extra_data': {
                        'request_id': request_id,
                        'error': str(e),
                    }
                }
            )
            raise
        finally:
            # Log response
            duration = time.time() - start_time
            self.logger.info(
                "Request completed",
                extra={
                    'extra_data': {
                        'request_id': request_id,
                        'status_code': response_status,
                        'duration_ms': round(duration * 1000, 2),
                        'response_size': len(response_body),
                    }
                }
            )

# Custom logger for business events
def log_business_event(event_type: str, user_id: int = None, data: Dict[str, Any] = None):
    """Log important business events"""
    logger = logging.getLogger('business_events')
    logger.info(
        f"Business Event: {event_type}",
        extra={
            'extra_data': {
                'event_type': event_type,
                'user_id': user_id,
                'data': data or {},
                'timestamp': datetime.utcnow().isoformat(),
            }
        }
    )
