import time
import pytest

from hw4_tourguide.tools.search import SearchTool
from hw4_tourguide.tools.fetch import FetchTool


class SlowClient:
    def __init__(self, delay: float = 0.05):
        self.delay = delay

    def search_videos(self, query, limit, location=None, radius_km=None, **kwargs):
        time.sleep(self.delay)
        return [{"id": f"v{i}"} for i in range(limit + 2)]

    def search_tracks(self, query, limit, **kwargs):
        time.sleep(self.delay)
        return [{"id": f"t{i}"} for i in range(limit + 2)]

    def search_articles(self, query, limit, **kwargs):
        time.sleep(self.delay)
        return [{"id": f"a{i}"} for i in range(limit + 2)]

    def fetch_video(self, video_id, **kwargs):
        time.sleep(self.delay)
        return {"id": video_id}

    def fetch_track(self, track_id, **kwargs):
        time.sleep(self.delay)
        return {"id": track_id}

    def fetch_article(self, article_id, **kwargs):
        time.sleep(self.delay)
        return {"id": article_id}


@pytest.mark.resilience
def test_search_limit_and_timeout():
    # limit enforcement
    search_tool = SearchTool(timeout=0.5)
    client = SlowClient(delay=0.01)
    results = search_tool.search_videos(client, query="test", limit=3)
    assert len(results) == 3

    # timeout
    slow_client = SlowClient(delay=0.2)
    search_tool_timeout = SearchTool(timeout=0.05)
    with pytest.raises(TimeoutError):
        search_tool_timeout.search_tracks(slow_client, query="slow", limit=2)


@pytest.mark.resilience
def test_fetch_timeout_and_success():
    fetch_tool = FetchTool(timeout=0.5)
    client = SlowClient(delay=0.01)
    assert fetch_tool.fetch_video(client, "vid")["id"] == "vid"

    slow_client = SlowClient(delay=0.2)
    fetch_tool_timeout = FetchTool(timeout=0.05)
    with pytest.raises(TimeoutError):
        fetch_tool_timeout.fetch_article(slow_client, "aid")
