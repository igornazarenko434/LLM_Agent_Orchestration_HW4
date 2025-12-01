import unittest
import sys
import os
from unittest.mock import MagicMock
import pytest
import hw4_tourguide.agents.song_agent as sa_module
from hw4_tourguide.agents.song_agent import SongAgent

@pytest.mark.unit
class TestSongAgentFallback(unittest.TestCase):
    def test_fallback_to_secondary_client(self):
        print(f"SongAgent loaded from: {sa_module.__file__}")
        
        mock_secondary = MagicMock()
        mock_secondary.search_tracks.return_value = [{"id": "yt_1", "title": "YouTube Song"}]
        mock_secondary.provider_name = "youtube"

        config = {"timeout": 1.0, "use_secondary_source": True}
        
        agent = SongAgent(
            config=config,
            client=None,
            secondary_client=mock_secondary
        )

        self.assertEqual(agent.client, mock_secondary, "Secondary client should be promoted to primary")

if __name__ == '__main__':
    unittest.main()