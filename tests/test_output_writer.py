# tests/test_output_writer.py

import unittest
from unittest.mock import MagicMock, mock_open, patch
from pathlib import Path
import json
import csv
from datetime import datetime
import shutil
import logging
import pytest

from hw4_tourguide.output_writer import OutputWriter
from hw4_tourguide.file_interface import CheckpointWriter

@pytest.mark.unit
class TestOutputWriter(unittest.TestCase):

    def setUp(self):
        """Set up mock objects and sample data for each test."""
        # Patch get_logger within setUp and manage its lifecycle
        self.mock_get_logger_patcher = patch('hw4_tourguide.output_writer.get_logger')
        self.mock_get_logger = self.mock_get_logger_patcher.start() # This is the mock for get_logger itself
        
        self.mock_logger_instance = MagicMock(spec=logging.Logger)
        self.mock_get_logger.return_value = self.mock_logger_instance # Configure get_logger mock to return our instance
        
        self.mock_checkpoint_writer = MagicMock(spec=CheckpointWriter)
        
        # Create temporary paths for output files
        self.output_dir = Path("tmp_test_output")
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.json_path = self.output_dir / "test_output.json"
        self.report_path = self.output_dir / "test_report.md"
        self.csv_path = self.output_dir / "test_output.csv"

        self.output_writer = OutputWriter(
            json_path=self.json_path,
            report_path=self.report_path,
            csv_path=self.csv_path,
            checkpoint_writer=self.mock_checkpoint_writer,
        )

        self.sample_steps = [
            {
                "transaction_id": "tid-001",
                "step_number": 1,
                "location": "Boston Common",
                "instructions": "Walk straight ahead",
                "agents": {
                    "video": {"agent_type": "video", "status": "success", "metadata": {"title": "Boston Common Tour", "url": "http://youtube.com/bc", "description": "Desc Video"}},
                    "song": {"agent_type": "song", "status": "success", "metadata": {"title": "Dirty Water", "artist": "The Standells", "url": "http://spotify.com/dw"}},
                    "knowledge": {"agent_type": "knowledge", "status": "failure", "metadata": {}}
                },
                "judge": {
                    "overall_score": 85.0,
                    "chosen_agent": "video",
                    "individual_scores": {"video": 85.0, "song": 70.0, "knowledge": 0.0},
                    "rationale": "Video is highly relevant.",
                    "chosen_content": {"title": "Boston Common Tour", "url": "http://youtube.com/bc"}
                }
            },
            {
                "transaction_id": "tid-002",
                "step_number": 2,
                "location": "MIT Campus",
                "instructions": "Turn left",
                "agents": {
                    "video": {"agent_type": "video", "status": "failure", "metadata": {}},
                    "song": {"agent_type": "song", "status": "success", "metadata": {"title": "MIT Anthem", "artist": "MIT Students", "url": "http://mit.edu/anthem"}},
                    "knowledge": {"agent_type": "knowledge", "status": "success", "metadata": {"title": "History of MIT", "summary": "Wikipedia article", "url": "http://wikipedia.org/mit"}}
                },
                "judge": {
                    "overall_score": 90.0,
                    "chosen_agent": "knowledge",
                    "individual_scores": {"video": 0.0, "song": 75.0, "knowledge": 90.0},
                    "rationale": "Knowledge article provides rich historical context.",
                    "chosen_content": {"title": "History of MIT", "url": "http://wikipedia.org/mit"}
                }
            }
        ]

    def tearDown(self):
        """Clean up temporary files and directories."""
        self.mock_get_logger_patcher.stop() # Stop the patcher

        if self.output_dir.exists():
            shutil.rmtree(self.output_dir) # Use rmtree to remove non-empty directories


    def test_init(self):
        """Test initialization creates directories."""
        self.assertTrue(self.output_dir.is_dir())
        # Check that get_logger was called by OutputWriter's __init__
        self.mock_get_logger.assert_called_once_with("output")
        # Removed: self.mock_logger_instance.info.assert_called() - OutputWriter.__init__ doesn't log info

    def test_write_json(self):
        """Test writing JSON output."""
        written_path = self.output_writer.write_json(self.sample_steps)
        self.assertTrue(written_path.exists())
        self.assertEqual(written_path, self.json_path)

        with open(self.json_path, 'r') as f:
            content = json.load(f)
            self.assertEqual(len(content), len(self.sample_steps))
            self.assertEqual(content[0]["location"], "Boston Common")
        
        self.mock_checkpoint_writer.write.assert_called_once_with(
            "tid-001", "05_final_output.json", self.sample_steps
        )
        self.mock_logger_instance.info.assert_any_call(
            "WROTE JSON | tmp_test_output/test_output.json", extra={'event_tag': 'Output'}
        )

    def test_write_json_empty_steps(self):
        """Test writing JSON output with empty steps."""
        written_path = self.output_writer.write_json([])
        self.assertTrue(written_path.exists())
        with open(self.json_path, 'r') as f:
            content = json.load(f)
            self.assertEqual(len(content), 0)
        
        self.mock_checkpoint_writer.write.assert_not_called()
        self.mock_logger_instance.info.assert_any_call(
            "WROTE JSON | tmp_test_output/test_output.json", extra={'event_tag': 'Output'}
        )

    def test_write_report(self):
        """Test writing Markdown report."""
        written_path = self.output_writer.write_report(self.sample_steps)
        self.assertTrue(written_path.exists())
        self.assertEqual(written_path, self.report_path)

        content = written_path.read_text()
        self.assertIn("# Tour Guide System Report", content)
        self.assertIn(f"Generated on: {datetime.now().year}", content) # Check for year
        self.assertIn("## Step 1: Boston Common", content)
        self.assertIn("Chosen Content Type: **Video**", content)
        self.assertIn("[Boston Common Tour](http://youtube.com/bc)", content)
        self.assertIn("Overall Score: `85.0`", content)
        self.assertIn("Rationale: Video is highly relevant.", content)
        self.assertIn("## Step 2: MIT Campus", content)
        self.assertIn("Chosen Content Type: **Knowledge**", content)
        self.assertIn("[History of MIT](http://wikipedia.org/mit)", content)
        self.assertNotIn("No suitable content found", content) # Both steps have content

    def test_write_report_no_chosen_content(self):
        """Test Markdown report when judge finds no suitable content."""
        steps_no_content = [
            {
                "transaction_id": "tid-003",
                "step_number": 1,
                "location": "Nowhere",
                "instructions": "Go nowhere",
                "agents": {},
                "judge": {
                    "overall_score": -1.0,
                    "chosen_agent": None,
                    "individual_scores": {"video": 0.0, "song": 0.0, "knowledge": 0.0},
                    "rationale": "No suitable content found.",
                    "chosen_content": {}
                }
            }
        ]
        written_path = self.output_writer.write_report(steps_no_content)
        content = written_path.read_text()
        self.assertIn("No suitable content found for this step.", content)

    def test_write_csv(self):
        """Test writing CSV export."""
        written_path = self.output_writer.write_csv(self.sample_steps)
        self.assertTrue(written_path.exists())
        self.assertEqual(written_path, self.csv_path)

        with open(self.csv_path, 'r', newline='') as f:
            reader = csv.reader(f)
            headers = next(reader)
            self.assertEqual(headers, [
                "location",
                "video_title", "video_url", "video_score",
                "song_title", "song_url", "song_score",
                "knowledge_title", "knowledge_url", "knowledge_score",
                "judge_overall_score", "judge_chosen_agent", "judge_chosen_content_title", "judge_chosen_content_url"
            ])
            
            rows = list(reader)
            self.assertEqual(len(rows), 2)
            
            # Check first row (Boston Common)
            self.assertEqual(rows[0][0], "Boston Common") # location
            self.assertEqual(rows[0][1], "Boston Common Tour") # video_title
            self.assertEqual(rows[0][2], "http://youtube.com/bc") # video_url
            self.assertEqual(float(rows[0][3]), 85.0) # video_score
            self.assertEqual(rows[0][4], "Dirty Water") # song_title
            self.assertEqual(rows[0][5], "http://spotify.com/dw") # song_url
            self.assertEqual(float(rows[0][6]), 70.0) # song_score
            self.assertEqual(rows[0][7], "") # knowledge_title (failed)
            self.assertEqual(rows[0][8], "") # knowledge_url
            self.assertEqual(float(rows[0][9]), 0.0) # knowledge_score
            # Indices shifted due to removed rationales
            self.assertEqual(float(rows[0][10]), 85.0) # judge_overall_score
            self.assertEqual(rows[0][11], "video") # judge_chosen_agent
            self.assertEqual(rows[0][12], "Boston Common Tour") # judge_chosen_content_title
            self.assertEqual(rows[0][13], "http://youtube.com/bc") # judge_chosen_content_url

            # Check second row (MIT Campus)
            self.assertEqual(rows[1][0], "MIT Campus") # location
            self.assertEqual(rows[1][1], "") # video_title (failed)
            self.assertEqual(rows[1][3], "0.0") # video_score
            self.assertEqual(rows[1][4], "MIT Anthem") # song_title
            self.assertEqual(rows[1][6], "75.0") # song_score
            self.assertEqual(rows[1][7], "History of MIT") # knowledge_title
            self.assertEqual(rows[1][9], "90.0") # knowledge_score
            self.assertEqual(rows[1][10], "90.0") # judge_overall_score
            self.assertEqual(rows[1][11], "knowledge") # judge_chosen_agent

    def test_write_csv_empty_steps(self):
        """Test writing CSV export with empty steps."""
        written_path = self.output_writer.write_csv([])
        self.assertTrue(written_path.exists())

        with open(self.csv_path, 'r', newline='') as f:
            reader = csv.reader(f)
            headers = next(reader)
            self.assertEqual(headers, [
                "location",
                "video_title", "video_url", "video_score",
                "song_title", "song_url", "song_score",
                "knowledge_title", "knowledge_url", "knowledge_score",
                "judge_overall_score", "judge_chosen_agent", "judge_chosen_content_title", "judge_chosen_content_url"
            ])
            rows = list(reader)
            self.assertEqual(len(rows), 0)
