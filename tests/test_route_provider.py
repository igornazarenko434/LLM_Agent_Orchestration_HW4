import json
from pathlib import Path
import pytest
import requests

from hw4_tourguide.route_provider import CachedRouteProvider, GoogleMapsProvider


@pytest.mark.unit
def test_cached_route_provider_loads_and_writes_checkpoint(tmp_path: Path):
    route_file = tmp_path / "route.json"
    route_data = {
        "transaction_id": "tid123",
        "steps": [
            {
                "step_number": 1,
                "location_name": "Start",
                "coordinates": {"lat": 0, "lng": 0},
                "instructions": "Go",
            }
        ],
        "metadata": {"distance": "1 km", "duration": "1 min"},
    }
    route_file.write_text(json.dumps(route_data))

    checkpoint_dir = tmp_path / "checkpoints"
    provider = CachedRouteProvider(
        cache_dir=tmp_path,
        route_file=route_file,
        checkpoints_enabled=True,
        checkpoint_dir=checkpoint_dir,
    )

    payload = provider.get_route("A", "B")
    tasks = payload["tasks"]
    assert tasks[0]["location_name"] == "Start"
    checkpoint_path = checkpoint_dir / payload["metadata"]["transaction_id"] / "00_route.json"
    assert checkpoint_path.exists()


@pytest.mark.unit
def test_cached_route_provider_missing_file_raises(tmp_path: Path):
    provider = CachedRouteProvider(
        cache_dir=tmp_path,
        route_file=tmp_path / "missing.json",
        checkpoints_enabled=False,
    )
    with pytest.raises(FileNotFoundError):
        provider.get_route("A", "B")


@pytest.mark.unit
def test_cached_route_provider_malformed_json(tmp_path: Path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not valid")
    provider = CachedRouteProvider(
        cache_dir=tmp_path,
        route_file=bad_file,
        checkpoints_enabled=False,
    )
    with pytest.raises(ValueError):
        provider.get_route("A", "B")


@pytest.mark.unit
def test_google_maps_provider_transforms_response(monkeypatch, tmp_path: Path):
    fake_directions_response = {
        "status": "OK",
        "routes": [
          {
            "legs": [
              {
                "distance": {"text": "1 km"},
                "duration": {"text": "2 mins"},
                "steps": [
                  {
                    "end_location": {"lat": 1.0, "lng": 2.0},
                    "html_instructions": "Head north on <b>Main St</b>"
                  }
                ]
              }
            ]
          }
        ]
    }

    fake_geocoding_response = {
        "status": "OK",
        "results": [
            {
                "formatted_address": "Point A, City, State, USA",
                "address_components": [
                    {"long_name": "Point A", "types": ["intersection", "point_of_interest"]},
                    {"long_name": "City", "types": ["locality"]},
                ]
            }
        ]
    }

    class DummyResp:
        def __init__(self, data):
            self._data = data
        def raise_for_status(self): return None
        def json(self): return self._data

    calls = {"directions": 0, "geocoding": 0}

    def fake_get(url, *args, **kwargs):
        # Mock different responses based on API endpoint
        if "directions" in url:
            calls["directions"] += 1
            return DummyResp(fake_directions_response)
        elif "geocode" in url:
            calls["geocoding"] += 1
            return DummyResp(fake_geocoding_response)
        else:
            raise ValueError(f"Unexpected URL: {url}")

    monkeypatch.setattr("hw4_tourguide.route_provider.requests.get", fake_get)

    provider = GoogleMapsProvider(
        api_key="test",
        checkpoints_enabled=False,
        checkpoint_dir=tmp_path / "checkpoints",
    )
    payload = provider.get_route("A", "B")
    step = payload["tasks"][0]
    assert payload["metadata"]["distance"] == "1 km"
    assert step["location_name"] == "Point A"
    assert step["address"] == "Point A, City, State, USA"
    assert step["instructions"] == "Head north on Main St"
    assert step["search_hint"] == "Point A, B"
    assert payload["metadata"]["route_context"] == "B"
    assert calls["directions"] == 1
    assert calls["geocoding"] == 1


@pytest.mark.unit
def test_google_maps_provider_retries_on_failure(monkeypatch, tmp_path: Path):
    fake_response = {"status": "OK", "routes": [{"legs": [{"distance": {"text": "1 km"}, "duration": {"text": "2 mins"}, "steps": []}]}]}
    class DummyResp:
        def __init__(self, data): self._data = data
        def raise_for_status(self): return None
        def json(self): return self._data
    calls = {"count": 0}
    def fake_get(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise requests.RequestException("network down")
        return DummyResp(fake_response)

    monkeypatch.setattr("hw4_tourguide.route_provider.requests.get", fake_get)

    provider = GoogleMapsProvider(
        api_key="test",
        retry_attempts=2,
        checkpoints_enabled=False,
        checkpoint_dir=tmp_path / "checkpoints",
    )
    payload = provider.get_route("A", "B")
    assert calls["count"] == 2
    assert payload["metadata"]["distance"] == "1 km"


@pytest.mark.unit
def test_cached_route_provider_preserves_search_hint_and_context(tmp_path: Path):
    route_file = tmp_path / "route.json"
    route_data = {
        "transaction_id": "tid123",
        "route_context": "B",
        "steps": [
            {
                "step_number": 1,
                "location_name": "Point A",
                "instructions": "Head north",
                "coordinates": {"lat": 0, "lng": 0},
                "search_hint": "Point A, B",
            }
        ],
        "metadata": {"distance": "1 km", "duration": "1 min"},
    }
    route_file.write_text(json.dumps(route_data))
    provider = CachedRouteProvider(
        cache_dir=tmp_path,
        route_file=route_file,
        checkpoints_enabled=False,
    )
    payload = provider.get_route("A", "B")
    step = payload["tasks"][0]
    assert payload["metadata"]["route_context"] == "B"
    assert step["search_hint"] == "Point A, B"


@pytest.mark.unit
def test_google_maps_provider_accepts_route_within_step_limit(monkeypatch, tmp_path: Path):
    """Test that routes with ≤8 steps are accepted"""
    # Create a route with exactly 8 steps
    fake_response = {
        "status": "OK",
        "routes": [{
            "legs": [{
                "distance": {"text": "5 km"},
                "duration": {"text": "10 mins"},
                "steps": [
                    {"end_location": {"lat": float(i), "lng": float(i)}, "html_instructions": f"Step {i}"}
                    for i in range(1, 9)  # 8 steps
                ]
            }]
        }]
    }

    fake_geocoding = {
        "status": "OK",
        "results": [{
            "formatted_address": "Test Address",
            "address_components": [{"long_name": "TestPlace", "types": ["point_of_interest"]}]
        }]
    }

    class DummyResp:
        def __init__(self, data): self._data = data
        def raise_for_status(self): return None
        def json(self): return self._data

    def fake_get(url, *args, **kwargs):
        if "directions" in url:
            return DummyResp(fake_response)
        elif "geocode" in url:
            return DummyResp(fake_geocoding)

    monkeypatch.setattr("hw4_tourguide.route_provider.requests.get", fake_get)

    provider = GoogleMapsProvider(
        api_key="test",
        max_steps=8,
        checkpoints_enabled=False,
        checkpoint_dir=tmp_path / "checkpoints",
    )

    # Should succeed without raising an error
    payload = provider.get_route("A", "B")
    assert len(payload["tasks"]) == 8


@pytest.mark.unit
def test_google_maps_provider_rejects_route_exceeding_step_limit(monkeypatch, tmp_path: Path):
    """Test that routes with >8 steps are rejected with clear error message"""
    # Create a route with 12 steps (exceeds limit of 8)
    fake_response = {
        "status": "OK",
        "routes": [{
            "legs": [{
                "distance": {"text": "10 km"},
                "duration": {"text": "20 mins"},
                "steps": [
                    {"end_location": {"lat": float(i), "lng": float(i)}, "html_instructions": f"Step {i}"}
                    for i in range(1, 13)  # 12 steps
                ]
            }]
        }]
    }

    class DummyResp:
        def __init__(self, data): self._data = data
        def raise_for_status(self): return None
        def json(self): return self._data

    def fake_get(url, *args, **kwargs):
        return DummyResp(fake_response)

    monkeypatch.setattr("hw4_tourguide.route_provider.requests.get", fake_get)

    provider = GoogleMapsProvider(
        api_key="test",
        max_steps=8,
        checkpoints_enabled=False,
        checkpoint_dir=tmp_path / "checkpoints",
    )

    # Should raise ValueError with helpful message
    with pytest.raises(ValueError) as exc_info:
        provider.get_route("A", "B")

    error_message = str(exc_info.value)
    assert "12 steps" in error_message
    assert "exceeds the configured maximum of 8 steps" in error_message
    assert "YouTube API quota" in error_message
    assert "Please choose a shorter route" in error_message
