"""
Stub Route Provider for walking skeleton (Mission M7.0).

Returns a deterministic 3-step route without external API calls to validate
the threaded pipeline early.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
import uuid


class StubRouteProvider:
    """Return a canned route with three steps as task list."""

    def get_route(self, origin: str, destination: str) -> Dict[str, Any]:
        tid = f"{datetime.now(timezone.utc).isoformat()}_{uuid.uuid4().hex[:8]}"
        route_context = destination or origin
        tasks: List[Dict[str, Any]] = [
            {
                "transaction_id": tid,
                "step_number": 1,
                "location_name": origin or "Origin",
                "coordinates": {"lat": 0.0, "lng": 0.0},
                "instructions": "Start",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "search_hint": f"{origin}, {route_context}" if origin else route_context,
                "route_context": route_context,
            },
            {
                "transaction_id": tid,
                "step_number": 2,
                "location_name": "Midpoint",
                "coordinates": {"lat": 0.5, "lng": 0.5},
                "instructions": "Continue straight",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "search_hint": f"Midpoint, {route_context}",
                "route_context": route_context,
            },
            {
                "transaction_id": tid,
                "step_number": 3,
                "location_name": destination or "Destination",
                "coordinates": {"lat": 1.0, "lng": 1.0},
                "instructions": "Arrive",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "search_hint": f"{destination}, {route_context}" if destination else route_context,
                "route_context": route_context,
            },
        ]
        return {
            "tasks": tasks,
            "metadata": {
                "origin": origin,
                "destination": destination,
                "distance": "1 km",
                "duration": "3 mins",
                "transaction_id": tid,
                "route_context": route_context,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
