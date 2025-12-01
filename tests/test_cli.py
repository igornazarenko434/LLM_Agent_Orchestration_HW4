import subprocess
from pathlib import Path
import pytest


@pytest.mark.integration
def test_cli_help():
    result = subprocess.run([".venv/bin/python", "-m", "hw4_tourguide", "--help"], cwd=Path.cwd(), capture_output=True, text=True)
    assert result.returncode == 0
    assert "--from" in result.stdout
    assert "--to" in result.stdout
    assert "--mode" in result.stdout


@pytest.mark.integration
def test_cli_cached_run(tmp_path):
    output_path = tmp_path / "cli_route.json"
    result = subprocess.run(
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
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert output_path.exists()
