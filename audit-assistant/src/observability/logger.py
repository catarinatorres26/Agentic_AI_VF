# src/observability/logger.py

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Se houver extras (campos adicionais), inclui
        for key, value in record.__dict__.items():
            if key in ("args", "asctime", "created", "exc_info", "exc_text", "filename", "funcName",
                       "levelname", "levelno", "lineno", "module", "msecs", "msg", "name",
                       "pathname", "process", "processName", "relativeCreated", "stack_info",
                       "thread", "threadName"):
                continue
            if key not in payload:
                payload[key] = value

        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str = "audit-assistant") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # já configurado

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger
