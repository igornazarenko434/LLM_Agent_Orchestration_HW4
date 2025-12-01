"""
CLI entry coverage smoke (M7.17).
Ensures __main__.py wiring runs with patched scheduler/orchestrator/output to avoid long execution.
"""

from types import SimpleNamespace
from unittest import mock
import pytest

from hw4_tourguide import __main__ as cli


@pytest.mark.unit
def test_cli_entry_invokes_pipeline(monkeypatch, tmp_path):
    # Patch Scheduler to avoid real threading
    class _DummyScheduler:
        def __init__(self, *args, **kwargs):
            pass
        def start(self):
            return None
    monkeypatch.setattr(cli, "Scheduler", _DummyScheduler)

    # Patch Orchestrator to bypass worker threads
    class _DummyOrchestrator:
        def __init__(self, *args, **kwargs):
            pass
        def run(self):
            return []
    monkeypatch.setattr(cli, "Orchestrator", _DummyOrchestrator)

    # Patch OutputWriter to no-op
    class _DummyOutput:
        def __init__(self, *args, **kwargs):
            pass
        def write_json(self, *args, **kwargs):
            return None
        def write_report(self, *args, **kwargs):
            return None
        def write_csv(self, *args, **kwargs):
            return None
    monkeypatch.setattr(cli, "OutputWriter", _DummyOutput)

    args = SimpleNamespace(
        origin="Boston, MA",
        destination="Cambridge, MA",
        mode="cached",
        config=cli.Path("config/settings.yaml"),
        log_level="ERROR",
        output=str(tmp_path / "out.json"),
    )
    # Use real ConfigLoader but ensure secrets resolve to None
    config_loader = cli.ConfigLoader(config_path=args.config, cli_overrides={"logging.level": args.log_level})
    config = config_loader.get_all()
    exit_code = cli.run_pipeline(config, args, config_loader)
    assert exit_code == 0
