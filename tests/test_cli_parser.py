"""
CLI parser and main coverage (M7.17 CLI branch coverage).
"""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

from hw4_tourguide import __main__ as cli


@pytest.mark.unit
def test_cli_parser_defaults():
    parser = cli.create_parser()
    args = parser.parse_args(["--from", "A", "--to", "B"])
    assert args.origin == "A"
    assert args.destination == "B"
    assert args.mode == "cached"
    assert args.output == Path("output/final_route.json")


@pytest.mark.unit
def test_cli_main_cached_flow(monkeypatch, tmp_path):
    # Patch ConfigLoader to return minimal config
    class _FakeConfigLoader:
        def __init__(self, *args, **kwargs): pass
        def get_all(self):
            return {
                "scheduler": {"interval": 0.1},
                "orchestrator": {"max_workers": 1},
                "agents": {
                    "use_llm_for_queries": False,
                    "video": {"enabled": True},
                    "song": {"enabled": True},
                    "knowledge": {"enabled": True},
                },
                "judge": {},
                "output": {"checkpoint_dir": str(tmp_path / "checkpoints"), "checkpoints_enabled": False},
                "route_provider": {"cache_dir": str(tmp_path), "api_retry_attempts": 1, "api_timeout": 0.1},
                "metrics": {"enabled": False},
                "circuit_breaker": {"enabled": False},
            }
        def get_secret(self, key): return None
    monkeypatch.setattr(cli, "ConfigLoader", _FakeConfigLoader)
    monkeypatch.setattr(cli, "setup_logging", lambda *args, **kwargs: None)

    # Patch components to no-op
    monkeypatch.setattr(cli, "Scheduler", mock.MagicMock(start=lambda: None))
    monkeypatch.setattr(cli, "Orchestrator", mock.MagicMock(run=lambda self=None: []))
    monkeypatch.setattr(cli, "OutputWriter", mock.MagicMock(write_json=lambda *a, **k: None, write_report=lambda *a, **k: None, write_csv=lambda *a, **k: None))
    monkeypatch.setattr(cli, "_select_route_provider", lambda c, m, l, cp_dir, metrics: mock.MagicMock(get_route=lambda o, d: {"tasks": [], "metadata": {}}))
    monkeypatch.setattr(cli, "_build_agents", lambda *a, **k: {})
    monkeypatch.setattr(cli, "JudgeAgent", mock.MagicMock())

    args = SimpleNamespace(
        origin="A",
        destination="B",
        mode="cached",
        config=Path("config/settings.yaml"),
        log_level="INFO",
        output=str(tmp_path / "out.json"),
    )
    code = cli.run_pipeline(_FakeConfigLoader().get_all(), args, _FakeConfigLoader())
    assert code == 0


@pytest.mark.unit
def test_cli_logging_and_metrics(monkeypatch, tmp_path):
    """Exercise logging setup and metrics enabled path."""
    class _FakeConfigLoader:
        def __init__(self, *args, **kwargs): pass
        def get_all(self):
            return {
                "scheduler": {"interval": 0.1},
                "orchestrator": {"max_workers": 1},
                "agents": {"use_llm_for_queries": False, "video": {"enabled": True}, "song": {"enabled": True}, "knowledge": {"enabled": True}},
                "judge": {},
                "output": {"checkpoint_dir": str(tmp_path / "checkpoints"), "checkpoints_enabled": True},
                "route_provider": {"cache_dir": str(tmp_path), "api_retry_attempts": 1, "api_timeout": 0.1},
                "metrics": {"enabled": True, "file": str(tmp_path / "metrics.json"), "update_interval": 0.01},
                "circuit_breaker": {"enabled": False},
            }
        def get_secret(self, key): return None
    monkeypatch.setattr(cli, "ConfigLoader", _FakeConfigLoader)
    monkeypatch.setattr(cli, "setup_logging", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli, "Scheduler", mock.MagicMock(start=lambda: None))
    monkeypatch.setattr(cli, "Orchestrator", mock.MagicMock(run=lambda self=None: []))
    monkeypatch.setattr(cli, "OutputWriter", mock.MagicMock(write_json=lambda *a, **k: None, write_report=lambda *a, **k: None, write_csv=lambda *a, **k: None))
    monkeypatch.setattr(cli, "_select_route_provider", lambda c, m, l, cp_dir, metrics: mock.MagicMock(get_route=lambda o, d: {"tasks": [], "metadata": {}}))
    monkeypatch.setattr(cli, "_build_agents", lambda *a, **k: {})
    monkeypatch.setattr(cli, "JudgeAgent", mock.MagicMock())

    args = SimpleNamespace(
        origin="A",
        destination="B",
        mode="cached",
        config=Path("config/settings.yaml"),
        log_level="DEBUG",
        output=str(tmp_path / "out.json"),
    )
    code = cli.run_pipeline(_FakeConfigLoader().get_all(), args, _FakeConfigLoader())
    assert code == 0


@pytest.mark.unit
def test_cli_main_live_fallback(monkeypatch):
    # Force live mode with missing key -> stub provider path
    parser = cli.create_parser()
    args = parser.parse_args(["--from", "A", "--to", "B", "--mode", "live"])

    class _FakeConfigLoader:
        def __init__(self, *args, **kwargs): pass
        def get_all(self):
            return {
                "scheduler": {"interval": 0.1},
                "orchestrator": {"max_workers": 1},
                "agents": {
                    "use_llm_for_queries": False,
                    "video": {"enabled": True},
                    "song": {"enabled": True},
                    "knowledge": {"enabled": True},
                },
                "judge": {},
                "output": {"checkpoint_dir": "output/checkpoints", "checkpoints_enabled": False},
                "route_provider": {"cache_dir": "data/routes", "api_retry_attempts": 1, "api_timeout": 0.1},
                "metrics": {"enabled": False},
                "circuit_breaker": {"enabled": False},
            }
        def get_secret(self, key): return None
    monkeypatch.setattr(cli, "ConfigLoader", _FakeConfigLoader)
    monkeypatch.setattr(cli, "setup_logging", lambda *args, **kwargs: None)
    monkeypatch.setattr(cli, "Scheduler", mock.MagicMock(start=lambda: None))
    monkeypatch.setattr(cli, "Orchestrator", mock.MagicMock(run=lambda self=None: []))
    monkeypatch.setattr(cli, "OutputWriter", mock.MagicMock(write_json=lambda *a, **k: None, write_report=lambda *a, **k: None, write_csv=lambda *a, **k: None))

    # Stub route providers
    monkeypatch.setattr(cli, "StubRouteProvider", mock.MagicMock(get_route=lambda self, o, d: {"tasks": [], "metadata": {}}))
    monkeypatch.setattr(cli, "GoogleMapsProvider", mock.MagicMock())
    monkeypatch.setattr(cli, "_build_agents", lambda *a, **k: {})
    monkeypatch.setattr(cli, "JudgeAgent", mock.MagicMock())

    code = cli.run_pipeline(_FakeConfigLoader().get_all(), args, _FakeConfigLoader())
    assert code == 0


@pytest.mark.unit
def test_cli_missing_config_handles_error(monkeypatch, capsys):
    # Simulate missing config file -> main should print error and return 1
    class _BadLoader:
        def __init__(self, *a, **k): raise FileNotFoundError("missing config")
    monkeypatch.setattr(cli, "ConfigLoader", _BadLoader)
    # Simulate argv for required args
    argv = ["prog", "--from", "A", "--to", "B"]
    monkeypatch.setattr(sys, "argv", argv)
    exit_code = cli.main()
    assert exit_code == 1
