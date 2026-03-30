import time
import psutil
import asyncio
from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock

@dataclass
class MetricPoint:
    timestamp: datetime
    value: float
    labels: Dict[str, str] = None

class MetricsCollector:
    """Advanced metrics collection and monitoring"""
    
    def __init__(self):
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._counters: Dict[str, int] = defaultdict(int)
        self._lock = Lock()
        
    def record_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a metric value"""
        with self._lock:
            self._metrics[name].append(
                MetricPoint(
                    timestamp=datetime.utcnow(),
                    value=value,
                    labels=labels or {}
                )
            )
    
    def increment_counter(self, name: str, labels: Dict[str, str] = None):
        """Increment a counter metric"""
        key = f"{name}:{str(sorted((labels or {}).items()))}"
        with self._lock:
            self._counters[key] += 1
    
    def get_metric_summary(self, name: str, hours: int = 1) -> Dict:
        """Get summary statistics for a metric"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        with self._lock:
            recent_points = [
                p for p in self._metrics[name] 
                if p.timestamp > cutoff
            ]
        
        if not recent_points:
            return {"count": 0}
        
        values = [p.value for p in recent_points]
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1],
            "timestamp": recent_points[-1].timestamp
        }
    
    def get_system_metrics(self) -> Dict:
        """Get current system metrics"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total": psutil.virtual_memory().total,
                "used": psutil.virtual_memory().used,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "used": psutil.disk_usage('/').used,
                "percent": psutil.disk_usage('/').percent
            },
            "processes": len(psutil.pids()),
            "timestamp": datetime.utcnow()
        }

# Global metrics collector
metrics = MetricsCollector()

class PerformanceMonitor:
    """Context manager for performance monitoring"""
    
    def __init__(self, operation_name: str, labels: Dict[str, str] = None):
        self.operation_name = operation_name
        self.labels = labels or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        # Record duration metric
        metrics.record_metric(
            f"operation_duration_{self.operation_name}",
            duration * 1000,  # Convert to milliseconds
            self.labels
        )
        
        # Record success/failure
        status = "success" if exc_type is None else "error"
        metrics.increment_counter(
            f"operation_count_{self.operation_name}",
            {**self.labels, "status": status}
        )

def monitor_performance(operation_name: str, labels: Dict[str, str] = None):
    """Decorator for monitoring function performance"""
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                with PerformanceMonitor(operation_name, labels):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                with PerformanceMonitor(operation_name, labels):
                    return func(*args, **kwargs)
            return sync_wrapper
    return decorator

# Background task for collecting system metrics
async def collect_system_metrics():
    """Background task to collect system metrics"""
    while True:
        try:
            sys_metrics = metrics.get_system_metrics()
            
            metrics.record_metric("system_cpu_percent", sys_metrics["cpu_percent"])
            metrics.record_metric("system_memory_percent", sys_metrics["memory"]["percent"])
            metrics.record_metric("system_disk_percent", sys_metrics["disk"]["percent"])
            metrics.record_metric("system_process_count", sys_metrics["processes"])
            
            await asyncio.sleep(60)  # Collect every minute
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to collect system metrics: {e}")
            await asyncio.sleep(60)
