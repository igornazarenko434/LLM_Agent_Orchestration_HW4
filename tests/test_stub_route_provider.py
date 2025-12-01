"""
StubRouteProvider coverage (M7.17 minor).
"""

import pytest
from hw4_tourguide.stub_route_provider import StubRouteProvider


@pytest.mark.unit
def test_stub_route_provider_outputs_steps():
    provider = StubRouteProvider()
    payload = provider.get_route("Origin", "Destination")
    assert payload["tasks"]
    assert payload["metadata"]["origin"] == "Origin"
