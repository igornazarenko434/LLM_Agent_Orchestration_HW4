"""
Stub agents for walking skeleton (Mission M7.0).
Return canned results without external API calls to validate concurrency plumbing.
"""

from typing import Dict, Any
from datetime import datetime, timezone
from hw4_tourguide.logger import get_logger


class BaseStubAgent:
    agent_type: str = "base"

    def __init__(self) -> None:
        self.logger = get_logger(f"agent.{self.agent_type}")
        self.logger.warning(
            f"{self.agent_type.title()} running in STUB mode (no live API)",
            extra={"event_tag": "Setup"},
        )

    def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Return a canned agent result."""
        now = datetime.now(timezone.utc).isoformat()
        location = task.get("location_name", "Unknown")
        result = {
            "agent_type": self.agent_type,
            "status": "ok",
            "metadata": {
                "title": f"{self.agent_type.title()} pick for {location}",
                "url": f"https://example.com/{self.agent_type}/{location}",
                "description": f"Canned {self.agent_type} content for {location}",
                "score": 80,
            },
            "reasoning": f"Stubbed {self.agent_type} result for {location}",
            "timestamp": now,
            "error": None,
        }
        self.logger.info(
            f"RETURN | {location}",
            extra={"event_tag": "Agent"},
        )
        return result


class VideoStubAgent(BaseStubAgent):
    agent_type = "video"


class SongStubAgent(BaseStubAgent):
    agent_type = "song"


class KnowledgeStubAgent(BaseStubAgent):
    agent_type = "knowledge"
