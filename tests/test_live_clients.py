import pytest
from hw4_tourguide.tools.youtube_client import YouTubeClient
from hw4_tourguide.tools.spotify_client import SpotifyClient
from hw4_tourguide.tools.wikipedia_client import WikipediaClient, DuckDuckGoClient


class MockResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("http error")

    def json(self):
        return self._payload


@pytest.mark.integration
def test_youtube_client_search(monkeypatch):
    payload = {"items": [{"id": {"videoId": "vid1"}, "snippet": {"title": "t", "channelTitle": "c", "publishedAt": "2024"}}]}
    monkeypatch.setattr("requests.get", lambda *a, **k: MockResponse(payload))
    client = YouTubeClient(api_key="key", timeout=0.1)
    results = client.search_videos("q", limit=1)
    assert results and results[0]["id"] == "vid1"


@pytest.mark.integration
def test_spotify_client_search(monkeypatch):
    # mock token fetch
    monkeypatch.setattr("requests.post", lambda *a, **k: MockResponse({"access_token": "tok", "expires_in": 3600}))
    # mock search call
    payload = {"tracks": {"items": [{"id": "tid", "name": "t", "artists": [{"name": "a"}], "album": {"name": "alb", "release_date": "2024"}, "duration_ms": 1, "preview_url": None, "external_urls": {"spotify": "url"}, "popularity": 1}]}}
    monkeypatch.setattr("requests.get", lambda *a, **k: MockResponse(payload))
    client = SpotifyClient(client_id="id", client_secret="secret", timeout=0.1)
    results = client.search_tracks("q", limit=1)
    assert results and results[0]["id"] == "tid"


@pytest.mark.integration
def test_wikipedia_client_search(monkeypatch):
    payload = {"query": {"search": [{"pageid": 123, "title": "Foo"}]}}
    monkeypatch.setattr("requests.get", lambda *a, **k: MockResponse(payload))
    client = WikipediaClient(timeout=0.1)
    results = client.search_articles("q", limit=1)
    assert results and results[0]["id"] == "123"


@pytest.mark.integration
def test_duckduckgo_client_search(monkeypatch):
    payload = {"AbstractURL": "http://x", "Heading": "H", "AbstractText": "T", "RelatedTopics": []}
    monkeypatch.setattr("requests.get", lambda *a, **k: MockResponse(payload))
    client = DuckDuckGoClient(timeout=0.1)
    results = client.search_articles("q", limit=1)
    assert results and results[0]["id"] == "http://x"
