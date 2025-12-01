"""
Route provider live path coverage (M7.17).
"""

import json
from unittest import mock
import pytest

from hw4_tourguide.route_provider import GoogleMapsProvider


@pytest.mark.integration
def test_route_provider_live_success(monkeypatch):
    fake_directions_resp = {
        "status": "OK",
        "routes": [
            {
                "legs": [
                    {
                        "distance": {"text": "1 mi"},
                        "duration": {"text": "2 mins"},
                        "steps": [
                            {
                                "end_address": "Dest",
                                "end_location": {"lat": 1.0, "lng": 2.0},
                                "html_instructions": "Turn <b>left</b>",
                            }
                        ],
                    }
                ]
            }
        ],
    }

    fake_geocoding_resp = {
        "status": "OK",
        "results": [
            {
                "formatted_address": "Test Location, City, State",
                "address_components": [
                    {"long_name": "Test Location", "types": ["point_of_interest", "establishment"]},
                    {"long_name": "City", "types": ["locality"]},
                ]
            }
        ]
    }

    class _Resp:
        def __init__(self, data):
            self._data = data
        def raise_for_status(self): return None
        def json(self): return self._data

    def fake_get(url, *args, **kwargs):
        if "directions" in url:
            return _Resp(fake_directions_resp)
        elif "geocode" in url:
            return _Resp(fake_geocoding_resp)
        else:
            return _Resp(fake_directions_resp)

    with mock.patch("requests.get", side_effect=fake_get):
        provider = GoogleMapsProvider(api_key="key", checkpoints_enabled=False)
        payload = provider.get_route("A", "B")
        assert payload["tasks"][0]["location_name"] == "Test Location"
        assert payload["tasks"][0]["coordinates"]["lat"] == 1.0
