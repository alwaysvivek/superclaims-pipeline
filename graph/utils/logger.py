import json
import logging
import time
from datetime import datetime, timezone

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "line": record.lineno,
        }
        
        # Include extra fields if present (like request_id)
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
        
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def setup_json_logging(level=logging.INFO):
    """Configure root logging to use JsonFormatter."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger.addHandler(handler)
    
    return root_logger

def get_json_logger(name: str, request_id: str = None):
    """Get a logger that includes request_id in every log context."""
    logger = logging.getLogger(name)
    if request_id:
        return logging.LoggerAdapter(logger, {"request_id": request_id})
    return logger
