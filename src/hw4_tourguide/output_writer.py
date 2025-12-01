"""
Output writer for the Tour-Guide System (Mission M7.8).
Writes JSON, Markdown report, and CSV export of enriched route steps.
"""

import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime # Added import

from hw4_tourguide.logger import get_logger
from hw4_tourguide.file_interface import CheckpointWriter


class OutputWriter:
    def __init__(
        self,
        json_path: Path,
        report_path: Path,
        csv_path: Path,
        checkpoint_writer: Optional[CheckpointWriter] = None,
    ):
        self.json_path = json_path
        self.report_path = report_path
        self.csv_path = csv_path
        self.checkpoint_writer = checkpoint_writer
        self.logger = get_logger("output")

        # Ensure parent directories exist for all output paths
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)

    def write_json(self, steps: List[Dict[str, Any]]) -> Path:
        """Writes the aggregated route steps to a JSON file."""
        steps = sorted(steps, key=lambda s: s.get("step_number", 0))
        self.json_path.write_text(json.dumps(steps, indent=2))
        self.logger.info(
            f"WROTE JSON | {self.json_path}",
            extra={"event_tag": "Output"},
        )

        # Also write the final aggregated result as a checkpoint
        if self.checkpoint_writer and steps:
            # Assuming all steps have the same transaction_id for the whole route
            # or we need to write one checkpoint per step, but the mission implies
            # a final_output.json for the whole route.
            # Let's use the first step's transaction_id for the route-level checkpoint
            # or generate a generic one if not available.
            transaction_id = steps[0].get("transaction_id", "overall_route") if steps else "overall_route"
            try:
                self.checkpoint_writer.write(
                    transaction_id, "05_final_output.json", steps
                )
                self.logger.info(
                    f"WROTE CHECKPOINT | {transaction_id}/05_final_output.json",
                    extra={"event_tag": "Output"},
                )
            except Exception as e:
                self.logger.error(
                    f"Failed to write final output checkpoint for {transaction_id}: {e}",
                    extra={"event_tag": "Error"},
                )

        return self.json_path

    def write_report(self, steps: List[Dict[str, Any]]) -> Path:
        """Generates a human-friendly Markdown summary report."""
        steps = sorted(steps, key=lambda s: s.get("step_number", 0))
        report_content = ["# Tour Guide System Report\n"]
        # Changed to use datetime.now() for robustness in testing
        report_content.append(f"Generated on: {datetime.now().isoformat()}\n") 

        for i, step in enumerate(steps):
            report_content.append(f"## Step {i+1}: {step.get('location', 'Unknown Location')}\n")
            report_content.append(f"Instructions: {step.get('instructions', 'N/A')}\n")
            
            judge_decision = step.get('judge', {})
            chosen_agent = judge_decision.get('chosen_agent')
            chosen_content = judge_decision.get('chosen_content', {})

            report_content.append(f"### Judge's Decision for {step.get('location', 'this step')}\n")
            if chosen_agent:
                report_content.append(f"Chosen Content Type: **{chosen_agent.capitalize()}**\n")
                report_content.append(f"Title: [{chosen_content.get('title', 'N/A')}]({chosen_content.get('url', '#')})\n")
                report_content.append(f"Overall Score: `{judge_decision.get('overall_score', 'N/A')}`\n")
                report_content.append(f"Rationale: {judge_decision.get('rationale', 'No rationale provided.')}\n")
                # Include per-agent rationales for explainability
                per_agent = judge_decision.get("per_agent_rationales", {})
                for agent_name, rationale in per_agent.items():
                    report_content.append(f"- {agent_name.title()} rationale: {rationale}\n")
            else:
                report_content.append("No suitable content found for this step.\n")
            
            report_content.append("\n---\n") # Separator between steps

        self.report_path.write_text("".join(report_content))
        self.logger.info(
            f"WROTE Markdown Report | {self.report_path}",
            extra={"event_tag": "Output"},
        )
        return self.report_path

    def write_csv(self, steps: List[Dict[str, Any]]) -> Path:
        """Generates a tabular CSV export for tour guides."""
        steps = sorted(steps, key=lambda s: s.get("step_number", 0))
        headers = [
            "location",
            "video_title", "video_url", "video_score",
            "song_title", "song_url", "song_score",
            "knowledge_title", "knowledge_url", "knowledge_score",
            "judge_overall_score", "judge_chosen_agent", "judge_chosen_content_title", "judge_chosen_content_url"
        ]
        
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            for step in steps:
                row_data = {header: "" for header in headers}
                row_data["location"] = step.get("location", "N/A")

                # Extract agent results
                # Fix: Changed step.get("agents", {{}}) to step.get("agents", {})
                for agent_type, agent_output in step.get("agents", {}).items(): 
                    if agent_output.get("status") in {"ok", "success"} and agent_output.get("metadata"):
                        metadata = agent_output["metadata"]
                        row_data[f"{agent_type}_title"] = metadata.get("title", "N/A")
                        row_data[f"{agent_type}_url"] = metadata.get("url", "N/A")
                        # Agent-level score might not always be available/relevant to CSV
                        # row_data[f"{agent_type}_score"] = metadata.get("score", "")

                # Extract judge decision
                judge_decision = step.get('judge', {})
                row_data["judge_overall_score"] = judge_decision.get("overall_score", "N/A")
                row_data["judge_chosen_agent"] = judge_decision.get("chosen_agent", "N/A")
                
                chosen_content = judge_decision.get('chosen_content', {})
                row_data["judge_chosen_content_title"] = chosen_content.get("title", "N/A")
                row_data["judge_chosen_content_url"] = chosen_content.get("url", "N/A")

                # Individual scores from judge
                individual_scores = judge_decision.get('individual_scores', {})
                for agent_type in ['video', 'song', 'knowledge']:
                    row_data[f"{agent_type}_score"] = individual_scores.get(agent_type, "N/A")

                writer.writerow([row_data[header] for header in headers])

        self.logger.info(
            f"WROTE CSV Report | {self.csv_path}",
            extra={"event_tag": "Output"},
        )
        return self.csv_path
