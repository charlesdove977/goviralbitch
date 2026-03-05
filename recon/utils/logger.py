"""
Recon — Comprehensive Logging System
Logs to both console and file with structured error tracking.
Ported from ReelRecon with log directory adjusted to data/recon/logs/.
"""

import os
import sys
import time
import json
import hashlib
import traceback
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import Optional, Dict, Any
import threading


class LogLevel(Enum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class ReconLogger:
    """Thread-safe logger with file rotation and structured error codes"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, log_dir: Optional[Path] = None, max_file_size_mb: int = 10, max_files: int = 5):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.log_dir = log_dir or Path(__file__).parent.parent.parent / "data" / "recon" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.max_files = max_files
        self.min_level = LogLevel.DEBUG

        self.current_log_file = self.log_dir / "recon.log"
        self.error_log_file = self.log_dir / "errors.log"

        self.error_registry: Dict[str, Dict[str, Any]] = {}
        self._file_lock = threading.Lock()

        self._write_log(LogLevel.INFO, "SYSTEM", "Logger initialized", {
            "log_dir": str(self.log_dir),
            "pid": os.getpid()
        })

    def _generate_error_code(self, category: str, message: str) -> str:
        timestamp_part = int(time.time()) % 100000
        hash_part = hashlib.md5(f"{category}:{message}".encode()).hexdigest()[:4].upper()
        return f"{category}-{timestamp_part:05d}-{hash_part}"

    def _rotate_if_needed(self, log_file: Path):
        if not log_file.exists():
            return
        if log_file.stat().st_size < self.max_file_size:
            return
        for i in range(self.max_files - 1, 0, -1):
            old_file = log_file.with_suffix(f".{i}.log")
            new_file = log_file.with_suffix(f".{i+1}.log")
            if old_file.exists():
                if new_file.exists():
                    new_file.unlink()
                old_file.rename(new_file)
        backup = log_file.with_suffix(".1.log")
        if backup.exists():
            backup.unlink()
        log_file.rename(backup)

    def _format_log_entry(self, level: LogLevel, category: str, message: str,
                          data: Optional[Dict] = None, error_code: Optional[str] = None) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        entry = {
            "timestamp": timestamp,
            "level": level.name,
            "category": category,
            "message": message
        }
        if error_code:
            entry["error_code"] = error_code
        if data:
            entry["data"] = data
        return json.dumps(entry, ensure_ascii=False, default=str)

    def _write_log(self, level: LogLevel, category: str, message: str,
                   data: Optional[Dict] = None, error_code: Optional[str] = None):
        if level.value < self.min_level.value:
            return

        log_entry = self._format_log_entry(level, category, message, data, error_code)

        level_colors = {
            LogLevel.DEBUG: "\033[90m",
            LogLevel.INFO: "\033[0m",
            LogLevel.WARNING: "\033[93m",
            LogLevel.ERROR: "\033[91m",
            LogLevel.CRITICAL: "\033[95m"
        }
        reset = "\033[0m"
        color = level_colors.get(level, "")

        console_msg = f"[{category}] {message}"
        if error_code:
            console_msg = f"[{error_code}] {message}"
        print(f"{color}{console_msg}{reset}")

        with self._file_lock:
            try:
                self._rotate_if_needed(self.current_log_file)
                with open(self.current_log_file, 'a', encoding='utf-8') as f:
                    f.write(log_entry + "\n")
                if level.value >= LogLevel.ERROR.value:
                    self._rotate_if_needed(self.error_log_file)
                    with open(self.error_log_file, 'a', encoding='utf-8') as f:
                        f.write(log_entry + "\n")
            except Exception as e:
                print(f"[LOGGER ERROR] Failed to write log: {e}", file=sys.stderr)

    def debug(self, category: str, message: str, data: Optional[Dict] = None):
        self._write_log(LogLevel.DEBUG, category, message, data)

    def info(self, category: str, message: str, data: Optional[Dict] = None):
        self._write_log(LogLevel.INFO, category, message, data)

    def warning(self, category: str, message: str, data: Optional[Dict] = None):
        self._write_log(LogLevel.WARNING, category, message, data)

    def error(self, category: str, message: str, data: Optional[Dict] = None,
              exception: Optional[Exception] = None) -> str:
        error_code = self._generate_error_code(category, message)
        error_data = data or {}
        if exception:
            error_data["exception_type"] = type(exception).__name__
            error_data["exception_msg"] = str(exception)
            error_data["traceback"] = traceback.format_exc()
        self.error_registry[error_code] = {
            "category": category,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": error_data
        }
        self._write_log(LogLevel.ERROR, category, message, error_data, error_code)
        return error_code

    def critical(self, category: str, message: str, data: Optional[Dict] = None,
                 exception: Optional[Exception] = None) -> str:
        error_code = self._generate_error_code(category, message)
        error_data = data or {}
        if exception:
            error_data["exception_type"] = type(exception).__name__
            error_data["exception_msg"] = str(exception)
            error_data["traceback"] = traceback.format_exc()
        self.error_registry[error_code] = {
            "category": category,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": error_data,
            "critical": True
        }
        self._write_log(LogLevel.CRITICAL, category, message, error_data, error_code)
        return error_code

    def get_error_details(self, error_code: str) -> Optional[Dict]:
        return self.error_registry.get(error_code)

    def get_recent_errors(self, limit: int = 20) -> list:
        errors = list(self.error_registry.items())
        errors.sort(key=lambda x: x[1].get("timestamp", ""), reverse=True)
        return errors[:limit]


# Global logger instance
_logger: Optional[ReconLogger] = None


def get_logger() -> ReconLogger:
    """Get the global logger instance"""
    global _logger
    if _logger is None:
        _logger = ReconLogger()
    return _logger
