"""
DREDGE Monitoring and Metrics
Provides metrics collection, exporters, and distributed tracing support.
"""
import time
import logging
from typing import Dict, Any, Optional, List
from collections import defaultdict, deque
from datetime import datetime
import json

logger = logging.getLogger("DREDGE.Monitoring")


class MetricsCollector:
    """
    Collects and aggregates metrics for DREDGE operations.
    Provides Prometheus-compatible metric types.
    """
    
    def __init__(self):
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        logger.info("Initialized MetricsCollector")
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        key = self._make_key(name, labels)
        self.counters[key] += value
        logger.debug(f"Counter incremented: {key} (+{value})")
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric value."""
        key = self._make_key(name, labels)
        self.gauges[key] = value
        logger.debug(f"Gauge set: {key} = {value}")
    
    def observe_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a histogram observation."""
        key = self._make_key(name, labels)
        self.histograms[key].append(value)
        logger.debug(f"Histogram observation: {key} = {value}")
    
    def record_timer(self, name: str, duration: float, labels: Optional[Dict[str, str]] = None):
        """Record a timer duration in seconds."""
        key = self._make_key(name, labels)
        self.timers[key].append(duration)
        logger.debug(f"Timer recorded: {key} = {duration:.4f}s")
    
    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        """Create metric key from name and labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        return {
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'histograms': {k: self._summarize_histogram(v) for k, v in self.histograms.items()},
            'timers': {k: self._summarize_timer(v) for k, v in self.timers.items()}
        }
    
    def _summarize_histogram(self, values: List[float]) -> Dict[str, float]:
        """Summarize histogram values."""
        if not values:
            return {'count': 0, 'sum': 0.0, 'min': 0.0, 'max': 0.0, 'avg': 0.0}
        
        return {
            'count': len(values),
            'sum': sum(values),
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values)
        }
    
    def _summarize_timer(self, values: deque) -> Dict[str, float]:
        """Summarize timer values."""
        if not values:
            return {'count': 0, 'total_time': 0.0, 'min': 0.0, 'max': 0.0, 'avg': 0.0}
        
        values_list = list(values)
        return {
            'count': len(values_list),
            'total_time': sum(values_list),
            'min': min(values_list),
            'max': max(values_list),
            'avg': sum(values_list) / len(values_list)
        }
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []
        
        # Counters
        for key, value in self.counters.items():
            lines.append(f"# TYPE {key.split('{')[0]} counter")
            lines.append(f"{key} {value}")
        
        # Gauges
        for key, value in self.gauges.items():
            lines.append(f"# TYPE {key.split('{')[0]} gauge")
            lines.append(f"{key} {value}")
        
        # Histograms
        for key, values in self.histograms.items():
            base_name = key.split('{')[0]
            summary = self._summarize_histogram(values)
            lines.append(f"# TYPE {base_name} histogram")
            lines.append(f"{key}_count {summary['count']}")
            lines.append(f"{key}_sum {summary['sum']}")
        
        return "\n".join(lines) + "\n"
    
    def reset(self):
        """Reset all metrics."""
        count = len(self.counters) + len(self.gauges) + len(self.histograms) + len(self.timers)
        self.counters.clear()
        self.gauges.clear()
        self.histograms.clear()
        self.timers.clear()
        logger.info(f"Reset {count} metrics")


class Timer:
    """Context manager for timing operations."""
    
    def __init__(self, collector: MetricsCollector, name: str, labels: Optional[Dict[str, str]] = None):
        self.collector = collector
        self.name = name
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.collector.record_timer(self.name, duration, self.labels)
        return False


class TraceSpan:
    """Represents a trace span for distributed tracing."""
    
    def __init__(self, name: str, trace_id: Optional[str] = None, parent_id: Optional[str] = None):
        self.name = name
        self.trace_id = trace_id or self._generate_id()
        self.span_id = self._generate_id()
        self.parent_id = parent_id
        self.start_time = time.time()
        self.end_time = None
        self.tags: Dict[str, Any] = {}
        self.logs: List[Dict[str, Any]] = []
    
    def _generate_id(self) -> str:
        """Generate a unique ID for trace/span."""
        import random
        return f"{int(time.time() * 1000000)}{random.randint(1000, 9999)}"
    
    def set_tag(self, key: str, value: Any):
        """Set a tag on the span."""
        self.tags[key] = value
    
    def log(self, message: str, **kwargs):
        """Add a log entry to the span."""
        self.logs.append({
            'timestamp': time.time(),
            'message': message,
            **kwargs
        })
    
    def finish(self):
        """Finish the span."""
        self.end_time = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary."""
        return {
            'name': self.name,
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'parent_id': self.parent_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.end_time - self.start_time if self.end_time else None,
            'tags': self.tags,
            'logs': self.logs
        }


class Tracer:
    """Distributed tracing support for DREDGE operations."""
    
    def __init__(self):
        self.spans: List[TraceSpan] = []
        logger.info("Initialized Tracer")
    
    def start_span(self, name: str, trace_id: Optional[str] = None, 
                   parent_id: Optional[str] = None) -> TraceSpan:
        """Start a new trace span."""
        span = TraceSpan(name, trace_id, parent_id)
        self.spans.append(span)
        logger.debug(f"Started span: {name} (trace_id={span.trace_id})")
        return span
    
    def get_spans(self, trace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all spans, optionally filtered by trace_id."""
        if trace_id:
            return [s.to_dict() for s in self.spans if s.trace_id == trace_id]
        return [s.to_dict() for s in self.spans]
    
    def export_jaeger(self) -> List[Dict[str, Any]]:
        """Export spans in Jaeger-compatible format."""
        # Simplified Jaeger format
        return [
            {
                'traceID': span.trace_id,
                'spanID': span.span_id,
                'operationName': span.name,
                'startTime': int(span.start_time * 1000000),  # microseconds
                'duration': int((span.end_time - span.start_time) * 1000000) if span.end_time else 0,
                'tags': [{'key': k, 'value': v} for k, v in span.tags.items()],
                'logs': span.logs
            }
            for span in self.spans
        ]
    
    def clear(self):
        """Clear all spans."""
        count = len(self.spans)
        self.spans.clear()
        logger.info(f"Cleared {count} spans")


# Global instances
metrics_collector = MetricsCollector()
tracer = Tracer()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    return metrics_collector


def get_tracer() -> Tracer:
    """Get the global tracer."""
    return tracer
