"""
File-based interfaces and checkpoint writer (Mission M7.7a).

Provides lightweight JSON read/write utilities with basic schema key checks, plus
checkpoint helpers for ADR-009. Avoids extra dependencies by validating required
keys listed in the schema's "required" array only.
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from hw4_tourguide.logger import get_logger


class FileInterface:
    def __init__(self, logger_name: str = "file_interface") -> None:
        self.logger = get_logger(logger_name)

    def read_json(self, path: Path, schema: Optional[Path] = None) -> Any:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}") from exc
        if schema:
            self._validate_against_schema(data, schema)
        return data

    def write_json(self, path: Path, data: Any) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
        self.logger.info(f"Wrote JSON {path}", extra={"event_tag": "Output"})
        return path

    def _validate_against_schema(self, data: Any, schema_path: Path) -> None:
        if not schema_path.exists():
            self.logger.warning(f"Schema file not found: {schema_path}")
            return
        try:
            schema = json.loads(schema_path.read_text())
        except json.JSONDecodeError:
            self.logger.warning(f"Schema file invalid JSON: {schema_path}")
            return
        required = schema.get("required", [])
        if isinstance(required, list):
            missing = [key for key in required if key not in data]
            if missing:
                raise ValueError(f"Schema validation failed, missing keys: {missing}")


class CheckpointWriter:
    def __init__(
        self,
        base_dir: Path = Path("output/checkpoints"),
        retention_days: int = 7,
        logger_name: str = "checkpoint",
    ) -> None:
        self.base_dir = base_dir
        self.retention_days = retention_days
        self.logger = get_logger(logger_name)

    def write(self, transaction_id: str, stage_filename: str, data: Any) -> Path:
        path = self.base_dir / transaction_id / stage_filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
        self.logger.info(f"Wrote checkpoint {path}", extra={"event_tag": "Config"})
        return path

    def read(self, transaction_id: str, stage_filename: str) -> Any:
        path = self.base_dir / transaction_id / stage_filename
        if not path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {path}")
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise ValueError(f"Checkpoint invalid JSON: {path}") from exc

    def list(self, transaction_id: str) -> List[Path]:
        tid_dir = self.base_dir / transaction_id
        if not tid_dir.exists():
            return []
        return sorted([p for p in tid_dir.glob("*.json") if p.is_file()])

    def cleanup_old(self) -> List[Path]:
        if self.retention_days <= 0:
            return []
        now = time.time()
        cutoff = now - self.retention_days * 86400
        removed: List[Path] = []
        if not self.base_dir.exists():
            return removed
        for tid_dir in self.base_dir.iterdir():
            if not tid_dir.is_dir():
                continue
            for f in tid_dir.glob("*.json"):
                try:
                    if f.stat().st_mtime < cutoff:
                        f.unlink()
                        removed.append(f)
                except OSError:
                    continue
        if removed:
            self.logger.info(
                f"Removed {len(removed)} old checkpoints",
                extra={"event_tag": "Config"},
            )
        return removed
