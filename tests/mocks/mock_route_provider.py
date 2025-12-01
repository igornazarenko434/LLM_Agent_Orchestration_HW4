"""
Mock RouteProvider for tests.
Provides deterministic, quick-loading route data without external APIs.
"""

from typing import Dict, Any


class MockRouteProvider:
    def __init__(self, route: Dict[str, Any]) -> None:
        self._route = route

    def get_route(self, origin: str, destination: str) -> Dict[str, Any]:
        return self._route
