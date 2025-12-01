"""
Lightweight schema validation hooks for agent results and judge decisions.
Uses existing JSON schema files from docs/contracts but only enforces required keys
to avoid heavy dependencies.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from hw4_tourguide.logger import get_logger


class Validator:
    def __init__(self):
        self.logger = get_logger("validator")
        self.schemas = {
            "agent_result": Path("docs/contracts/agent_result_schema.json"),
            "judge_decision": Path("docs/contracts/judge_decision_schema.json"),
        }

    def validate_agent_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        schema = self._load_schema("agent_result")
        required = schema.get("required", [])
        filtered: List[Dict[str, Any]] = []
        for res in results:
            missing = [k for k in required if k not in res]
            if missing:
                self.logger.warning(
                    f"Agent result missing required fields {missing}",
                    extra={"event_tag": "Validator"},
                )
                continue
            filtered.append(res)
        return filtered

    def validate_judge_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        schema = self._load_schema("judge_decision")
        required = schema.get("required", [])
        missing = [k for k in required if k not in decision]
        if missing:
            self.logger.warning(
                f"Judge decision missing required fields {missing}",
                extra={"event_tag": "Validator"},
            )
        return decision

    def _load_schema(self, name: str) -> Dict[str, Any]:
        path = self.schemas.get(name)
        if not path or not path.exists():
            return {}
        try:
            return json.loads(path.read_text())
        except Exception:
            return {}
