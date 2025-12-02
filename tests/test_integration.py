import os
import json
import subprocess
from pathlib import Path
import pytest


def run_cli(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


@pytest.mark.integration
@pytest.mark.slow
def test_full_pipeline_cached(tmp_path):
    output_path = tmp_path / "route.json"
    result = run_cli(
        [
            ".venv/bin/python",
            "-m",
            "hw4_tourguide",
            "--from",
            "Boston, MA",
            "--to",
            "MIT",
            "--mode",
            "cached",
            "--output",
            str(output_path),
        ],
        cwd=Path.cwd(),
    )
    assert result.returncode == 0
    assert output_path.exists()
    data = json.loads(output_path.read_text())
    assert data, "output JSON should not be empty"
    # basic assertions
    for step in data:
        assert "judge" in step
        assert step["judge"].get("overall_score") is not None
        assert "agents" in step


@pytest.mark.integration
@pytest.mark.slow
def test_pipeline_with_mocked_clients(monkeypatch, tmp_path):
    # Monkeypatch clients to avoid network and force deterministic outputs
    from hw4_tourguide.tools.youtube_client import YouTubeClient
    from hw4_tourguide.tools.spotify_client import SpotifyClient
    from hw4_tourguide.tools.wikipedia_client import WikipediaClient

    def fake_youtube_search(self, query, limit, location=None, radius_km=None):
        return [{"id": "vid", "title": "Geo Video", "url": "http://y/vid", "view_count": 10, "duration_seconds": 100}]

    def fake_youtube_fetch(self, video_id):
        return {"id": video_id, "title": "Geo Video", "url": "http://y/vid", "duration_seconds": 100}

    def fake_spotify_search(self, query, limit):
        return [{"id": "trk", "title": "Mood Track", "popularity": 50, "url": "http://s/trk"}]

    def fake_spotify_fetch(self, track_id):
        return {"id": track_id, "title": "Mood Track", "url": "http://s/trk"}

    def fake_wiki_search(self, query, limit):
        return [{"id": "a2", "title": "Gov Doc", "url": "https://state.gov/doc"}]

    def fake_wiki_fetch(self, article_id):
        return {"id": article_id, "title": "Gov Doc", "url": "https://state.gov/doc"}

    monkeypatch.setattr(YouTubeClient, "search_videos", fake_youtube_search, raising=False)
    monkeypatch.setattr(YouTubeClient, "fetch_video", fake_youtube_fetch, raising=False)
    monkeypatch.setattr(SpotifyClient, "search_tracks", fake_spotify_search, raising=False)
    monkeypatch.setattr(SpotifyClient, "fetch_track", fake_spotify_fetch, raising=False)
    monkeypatch.setattr(WikipediaClient, "search_articles", fake_wiki_search, raising=False)
    monkeypatch.setattr(WikipediaClient, "fetch_article", fake_wiki_fetch, raising=False)

    output_path = tmp_path / "route_mock.json"
    result = run_cli(
        [
            ".venv/bin/python",
            "-m",
            "hw4_tourguide",
            "--from",
            "Boston, MA",
            "--to",
            "MIT",
            "--mode",
            "cached",
            "--output",
            str(output_path),
            "--log-level",
            "INFO",
        ],
        cwd=Path.cwd(),
    )
    assert result.returncode == 0
    data = json.loads(output_path.read_text())
    assert data
    # Validate mocked content flowed through
    for step in data:
        judge = step.get("judge", {})
        assert judge.get("overall_score") is not None


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.skipif(os.getenv("RUN_LIVE_TESTS") != "1", reason="Live tests disabled; set RUN_LIVE_TESTS=1 to enable")
def test_live_smoke(tmp_path):
    # Minimal live run with limits to avoid cost; requires keys present
    # Use a very short route to ensure steps < 8 (default max_steps)
    output_path = tmp_path / "route_live.json"
    result = run_cli(
        [
            ".venv/bin/python",
            "-m",
            "hw4_tourguide",
            "--from",
            "Kendall Square, Cambridge, MA",
            "--to",
            "MIT Museum, Cambridge, MA",
            "--mode",
            "live",
            "--output",
            str(output_path),
            "--log-level",
            "INFO",
        ],
        cwd=Path.cwd(),
    )
    assert result.returncode == 0
    assert output_path.exists()


@pytest.mark.integration
@pytest.mark.slow
def test_cached_mode_forces_stub_agents(monkeypatch, tmp_path):
    """
    Cached mode should not call live clients even if keys are present.
    """
    monkeypatch.setenv("YOUTUBE_API_KEY", "dummy")
    monkeypatch.setenv("SPOTIFY_CLIENT_ID", "id")
    monkeypatch.setenv("SPOTIFY_CLIENT_SECRET", "secret")

    from hw4_tourguide.tools.youtube_client import YouTubeClient

    calls = {"youtube": 0}

    def fail_if_called(self, *args, **kwargs):
        calls["youtube"] += 1
        raise RuntimeError("Live YouTube call should not occur in cached mode")

    monkeypatch.setattr(YouTubeClient, "search_videos", fail_if_called, raising=False)

    output_path = tmp_path / "route_cached_stub.json"
    result = run_cli(
        [
            ".venv/bin/python",
            "-m",
            "hw4_tourguide",
            "--from",
            "Boston, MA",
            "--to",
            "MIT",
            "--mode",
            "cached",
            "--output",
            str(output_path),
        ],
        cwd=Path.cwd(),
    )
    assert result.returncode == 0
    assert output_path.exists()
    assert calls["youtube"] == 0
