"""
route_provider.py error path coverage.
"""

import pytest
import requests
from unittest import mock

from hw4_tourguide.route_provider import GoogleMapsProvider


@pytest.mark.unit
def test_route_provider_invalid_response(monkeypatch):
    class _Resp:
        def raise_for_status(self): return None
        def json(self): return {"status": "OK", "routes": []}
    monkeypatch.setattr("requests.get", lambda *a, **k: _Resp())
    provider = GoogleMapsProvider(api_key="key", checkpoints_enabled=False)
    with pytest.raises(ValueError):
        provider.get_route("A", "B")


@pytest.mark.unit
def test_route_provider_timeout(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.Timeout("timeout")
    monkeypatch.setattr("requests.get", fake_get)
    provider = GoogleMapsProvider(api_key="key", retry_attempts=1, timeout=0.01, checkpoints_enabled=False)
    with pytest.raises(RuntimeError):
        provider.get_route("A", "B")
