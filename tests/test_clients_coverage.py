"""
Client wrapper coverage (M7.17).
"""

from unittest import mock
import pytest
import requests

from hw4_tourguide.tools.youtube_client import YouTubeClient
from hw4_tourguide.tools.spotify_client import SpotifyClient
from hw4_tourguide.tools.wikipedia_client import WikipediaClient


@pytest.mark.unit
def test_youtube_client_search_and_fetch(monkeypatch):
    search_payload = {"items": [{"id": {"videoId": "vid1"}, "snippet": {"title": "T", "channelTitle": "C", "publishedAt": "now"}}]}
    video_payload = {"items": [{"snippet": {"title": "T", "channelTitle": "C", "description": "D", "publishedAt": "now"}, "statistics": {"viewCount": "5"}, "contentDetails": {"duration": "PT1M"}}]}

    def fake_get(url, params=None, timeout=None):
        class _Resp:
            def raise_for_status(self): return None
            def json(self_inner):
                if "search" in url:
                    return search_payload
                return video_payload
        return _Resp()

    monkeypatch.setattr("requests.get", fake_get)
    client = YouTubeClient(api_key="k", timeout=0.1)
    results = client.search_videos("q", limit=1)
    assert results[0]["id"] == "vid1"
    meta = client.fetch_video("vid1")
    assert meta["title"] == "T"


@pytest.mark.unit
def test_spotify_client_search(monkeypatch):
    token_payload = {"access_token": "t", "expires_in": 3600}
    search_payload = {"tracks": {"items": [{"id": "id1", "name": "Song", "artists": [{"name": "A"}], "album": {"name": "Album", "release_date": "2020"}, "duration_ms": 1000, "preview_url": "u", "external_urls": {"spotify": "s"}, "popularity": 50}]}}

    def fake_post(url, data=None, auth=None, timeout=None):
        class _Resp:
            def raise_for_status(self): return None
            def json(self_inner): return token_payload
        return _Resp()

    def fake_get(url, headers=None, params=None, timeout=None):
        class _Resp:
            def raise_for_status(self): return None
            def json(self_inner): return search_payload
        return _Resp()

    monkeypatch.setattr("requests.post", fake_post)
    monkeypatch.setattr("requests.get", fake_get)
    client = SpotifyClient(client_id="id", client_secret="secret", timeout=0.1)
    results = client.search_tracks("q", limit=1)
    assert results[0]["id"] == "id1"


@pytest.mark.unit
def test_wikipedia_client_search_and_fetch(monkeypatch):
    search_payload = {"query": {"search": [{"pageid": 1, "title": "Page"}]}}
    fetch_payload = {"query": {"pages": {"1": {"title": "Page", "fullurl": "u", "extract": "summary"}}}}

    def fake_get(url, params=None, timeout=None, headers=None):
        class _Resp:
            def raise_for_status(self): return None
            def json(self_inner):
                if params.get("list") == "search":
                    return search_payload
                return fetch_payload
        return _Resp()

    monkeypatch.setattr("requests.get", fake_get)
    client = WikipediaClient(timeout=0.1)
    results = client.search_articles("q", limit=1)
    assert results[0]["id"] == "1"
    meta = client.fetch_article("1")
    assert meta["title"] == "Page"


@pytest.mark.unit
def test_youtube_client_handles_http_error(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        class _Resp:
            def raise_for_status(self): raise requests.HTTPError("500")
        return _Resp()
    monkeypatch.setattr("requests.get", fake_get)
    client = YouTubeClient(api_key="k", timeout=0.1)
    with pytest.raises(requests.HTTPError):
        client.search_videos("q", limit=1)


@pytest.mark.unit
def test_spotify_client_handles_bad_token(monkeypatch):
    def fake_post(url, data=None, auth=None, timeout=None):
        class _Resp:
            def raise_for_status(self): raise requests.HTTPError("401")
        return _Resp()
    monkeypatch.setattr("requests.post", fake_post)
    client = SpotifyClient(client_id="id", client_secret="secret", timeout=0.1)
    with pytest.raises(requests.HTTPError):
        client.search_tracks("q", limit=1)


@pytest.mark.unit
def test_wikipedia_client_handles_empty_response(monkeypatch):
    def fake_get(url, params=None, timeout=None, headers=None):
        class _Resp:
            def raise_for_status(self): return None
            def json(self_inner): return {"query": {"search": []}}
        return _Resp()
    monkeypatch.setattr("requests.get", fake_get)
    client = WikipediaClient(timeout=0.1)
    results = client.search_articles("q", limit=1)
    assert results == []
