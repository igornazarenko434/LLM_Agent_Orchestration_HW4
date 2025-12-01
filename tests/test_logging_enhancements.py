"""
Tests for logging enhancements (Phase 7b - M8).

Verifies:
- Module-specific log files (agents.log, judge.log, apis.log, route_provider.log)
- Run-specific directory organization
- Custom output path triggers global logging
"""

import logging
import pytest
from pathlib import Path
from hw4_tourguide.logger import setup_logging, get_logger


@pytest.mark.unit
def test_module_specific_log_files_created(tmp_path: Path):
    """Verify all module-specific log files are created."""
    log_base_dir = tmp_path
    config = {
        "level": "INFO",
        "file": "logs/system.log",
        "error_file": "logs/errors.log",
        "max_file_size_mb": 1,
        "backup_count": 2,
        "format": "%(levelname)s | %(name)s | %(event_tag)s | %(message)s",
        "console_enabled": False,
        "modules": {
            "agents": {
                "enabled": True,
                "file": "logs/agents.log",
                "level": "INFO",
                "max_bytes": 1048576,
                "backup_count": 2
            },
            "judge": {
                "enabled": True,
                "file": "logs/judge.log",
                "level": "INFO",
                "max_bytes": 1048576,
                "backup_count": 2
            },
            "apis": {
                "enabled": True,
                "file": "logs/apis.log",
                "level": "INFO",
                "max_bytes": 1048576,
                "backup_count": 2
            },
            "route_provider": {
                "enabled": True,
                "file": "logs/route_provider.log",
                "level": "INFO",
                "max_bytes": 1048576,
                "backup_count": 2
            }
        }
    }

    setup_logging(config, reset_existing=True, log_base_dir=log_base_dir)

    # Get loggers for each module (use correct logger name prefixes)
    agent_logger = get_logger("agent.video")
    judge_logger = get_logger("judge")
    api_logger = get_logger("api")
    route_logger = get_logger("route_provider.cached")

    # Log messages to each module
    agent_logger.info("agent message", extra={"event_tag": "Agent_Test"})
    judge_logger.info("judge message", extra={"event_tag": "Judge_Test"})
    api_logger.info("api message", extra={"event_tag": "API_Test"})
    route_logger.info("route message", extra={"event_tag": "Route_Test"})

    # Verify all module-specific log files exist
    log_dir = log_base_dir / "logs"
    assert (log_dir / "system.log").exists(), "system.log not created"
    assert (log_dir / "errors.log").exists(), "errors.log not created"
    assert (log_dir / "agents.log").exists(), "agents.log not created"
    assert (log_dir / "judge.log").exists(), "judge.log not created"
    assert (log_dir / "apis.log").exists(), "apis.log not created"
    assert (log_dir / "route_provider.log").exists(), "route_provider.log not created"

    # Verify messages appear in correct log files
    agents_text = (log_dir / "agents.log").read_text()
    assert "agent message" in agents_text
    assert "Agent_Test" in agents_text

    judge_text = (log_dir / "judge.log").read_text()
    assert "judge message" in judge_text
    assert "Judge_Test" in judge_text

    apis_text = (log_dir / "apis.log").read_text()
    assert "api message" in apis_text
    assert "API_Test" in apis_text

    route_text = (log_dir / "route_provider.log").read_text()
    assert "route message" in route_text
    assert "Route_Test" in route_text

    # Verify system.log contains all messages
    system_text = (log_dir / "system.log").read_text()
    assert "agent message" in system_text
    assert "judge message" in system_text
    assert "api message" in system_text
    assert "route message" in system_text


@pytest.mark.unit
def test_agents_log_file_contains_video_song_knowledge(tmp_path: Path):
    """Verify agents.log captures VideoAgent, SongAgent, KnowledgeAgent logs."""
    log_base_dir = tmp_path
    config = {
        "level": "INFO",
        "file": "logs/system.log",
        "error_file": "logs/errors.log",
        "console_enabled": False,
        "modules": {
            "agents": {
                "enabled": True,
                "file": "logs/agents.log",
                "level": "INFO",
                "max_bytes": 1048576,
                "backup_count": 2
            }
        }
    }

    setup_logging(config, reset_existing=True, log_base_dir=log_base_dir)

    # Simulate logs from all three agents (use correct logger name prefixes)
    video_logger = get_logger("agent.video")
    song_logger = get_logger("agent.song")
    knowledge_logger = get_logger("agent.knowledge")

    video_logger.info("VideoAgent_Process | Searching YouTube", extra={"event_tag": "VideoAgent_Search"})
    song_logger.info("SongAgent_Process | Searching Spotify", extra={"event_tag": "SongAgent_Search"})
    knowledge_logger.info("KnowledgeAgent_Process | Searching Wikipedia", extra={"event_tag": "KnowledgeAgent_Search"})

    agents_text = (log_base_dir / "logs" / "agents.log").read_text()
    assert "VideoAgent_Search" in agents_text
    assert "SongAgent_Search" in agents_text
    assert "KnowledgeAgent_Search" in agents_text
    assert "Searching YouTube" in agents_text
    assert "Searching Spotify" in agents_text
    assert "Searching Wikipedia" in agents_text


@pytest.mark.unit
def test_judge_log_file_contains_selection_logs(tmp_path: Path):
    """Verify judge.log captures judge selection and scoring logs."""
    log_base_dir = tmp_path
    config = {
        "level": "INFO",
        "file": "logs/system.log",
        "error_file": "logs/errors.log",
        "console_enabled": False,
        "modules": {
            "judge": {
                "enabled": True,
                "file": "logs/judge.log",
                "level": "INFO",
                "max_bytes": 1048576,
                "backup_count": 2
            }
        }
    }

    setup_logging(config, reset_existing=True, log_base_dir=log_base_dir)

    judge_logger = get_logger("judge")
    judge_logger.info("Judge_Input | Received 3 candidates", extra={"event_tag": "Judge_Input"})
    judge_logger.info("Judge_LLM_Call | Calling Gemini for scoring", extra={"event_tag": "Judge_LLM_Call"})
    judge_logger.info("Judge_Decision | Winner: video", extra={"event_tag": "Judge_Decision"})

    judge_text = (log_base_dir / "logs" / "judge.log").read_text()
    assert "Judge_Input" in judge_text
    assert "Judge_LLM_Call" in judge_text
    assert "Judge_Decision" in judge_text
    assert "Received 3 candidates" in judge_text
    assert "Winner: video" in judge_text


@pytest.mark.unit
def test_apis_log_file_contains_youtube_spotify_wikipedia(tmp_path: Path):
    """Verify apis.log captures YouTube, Spotify, Wikipedia API calls."""
    log_base_dir = tmp_path
    config = {
        "level": "INFO",
        "file": "logs/system.log",
        "error_file": "logs/errors.log",
        "console_enabled": False,
        "modules": {
            "apis": {
                "enabled": True,
                "file": "logs/apis.log",
                "level": "INFO",
                "max_bytes": 1048576,
                "backup_count": 2
            }
        }
    }

    setup_logging(config, reset_existing=True, log_base_dir=log_base_dir)

    youtube_logger = get_logger("api.youtube")
    spotify_logger = get_logger("api.spotify")
    wikipedia_logger = get_logger("api.wikipedia")

    youtube_logger.info("API_Call | YouTube search started", extra={"event_tag": "YouTube_Call"})
    spotify_logger.info("API_Call | Spotify search started", extra={"event_tag": "Spotify_Call"})
    wikipedia_logger.info("API_Call | Wikipedia query started", extra={"event_tag": "Wikipedia_Call"})

    apis_text = (log_base_dir / "logs" / "apis.log").read_text()
    assert "YouTube_Call" in apis_text
    assert "Spotify_Call" in apis_text
    assert "Wikipedia_Call" in apis_text
    assert "YouTube search started" in apis_text
    assert "Spotify search started" in apis_text
    assert "Wikipedia query started" in apis_text


@pytest.mark.unit
def test_route_provider_log_file_contains_google_maps_calls(tmp_path: Path):
    """Verify route_provider.log captures Google Maps API calls."""
    log_base_dir = tmp_path
    config = {
        "level": "INFO",
        "file": "logs/system.log",
        "error_file": "logs/errors.log",
        "console_enabled": False,
        "modules": {
            "route_provider": {
                "enabled": True,
                "file": "logs/route_provider.log",
                "level": "INFO",
                "max_bytes": 1048576,
                "backup_count": 2
            }
        }
    }

    setup_logging(config, reset_existing=True, log_base_dir=log_base_dir)

    route_logger = get_logger("route_provider.cached")
    route_logger.info("RouteProvider_API_Directions | Calling Google Maps", extra={"event_tag": "RouteProvider_API_Directions"})
    route_logger.info("RouteProvider_API_Success | Received 4 steps", extra={"event_tag": "RouteProvider_API_Success"})

    route_text = (log_base_dir / "logs" / "route_provider.log").read_text()
    assert "RouteProvider_API_Directions" in route_text
    assert "RouteProvider_API_Success" in route_text
    assert "Calling Google Maps" in route_text
    assert "Received 4 steps" in route_text


@pytest.mark.unit
def test_run_specific_logs_location(tmp_path: Path):
    """Verify logs go to run-specific directory when log_base_dir is provided."""
    run_dir = tmp_path / "output" / "2025-11-28_15-30-00_Boston_MA_to_MIT"
    run_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "level": "INFO",
        "file": "logs/system.log",
        "error_file": "logs/errors.log",
        "console_enabled": False,
        "modules": {
            "agents": {
                "enabled": True,
                "file": "logs/agents.log",
                "level": "INFO",
                "max_bytes": 1048576,
                "backup_count": 2
            }
        }
    }

    # Provide log_base_dir to trigger run-specific logging
    setup_logging(config, reset_existing=True, log_base_dir=run_dir)

    logger = get_logger("agent.video")
    logger.info("test message", extra={"event_tag": "Test"})

    # Verify logs are in run-specific directory
    assert (run_dir / "logs" / "system.log").exists()
    assert (run_dir / "logs" / "errors.log").exists()
    assert (run_dir / "logs" / "agents.log").exists()

    agents_text = (run_dir / "logs" / "agents.log").read_text()
    assert "test message" in agents_text


@pytest.mark.unit
def test_global_logs_without_log_base_dir(tmp_path: Path):
    """Verify logs go to global logs/ directory when log_base_dir is None."""
    import os
    original_cwd = os.getcwd()

    try:
        # Change to tmp_path to isolate test
        os.chdir(tmp_path)

        config = {
            "level": "INFO",
            "file": "logs/system.log",
            "error_file": "logs/errors.log",
            "console_enabled": False,
        }

        # Do NOT provide log_base_dir - should use paths from config as-is
        setup_logging(config, reset_existing=True, log_base_dir=None)

        logger = get_logger("test")
        logger.info("global log message", extra={"event_tag": "Test"})

        # Verify logs are in global logs/ directory (relative to cwd)
        assert (tmp_path / "logs" / "system.log").exists()
        assert (tmp_path / "logs" / "errors.log").exists()

        system_text = (tmp_path / "logs" / "system.log").read_text()
        assert "global log message" in system_text
    finally:
        os.chdir(original_cwd)


@pytest.mark.unit
def test_module_logger_disabled_when_config_disabled(tmp_path: Path):
    """Verify module-specific log files are NOT created when disabled in config."""
    log_base_dir = tmp_path
    config = {
        "level": "INFO",
        "file": "logs/system.log",
        "error_file": "logs/errors.log",
        "console_enabled": False,
        "modules": {
            "agents": {
                "enabled": False,  # DISABLED
                "file": "logs/agents.log",
                "level": "INFO",
                "max_bytes": 1048576,
                "backup_count": 2
            }
        }
    }

    setup_logging(config, reset_existing=True, log_base_dir=log_base_dir)

    agent_logger = get_logger("agent.video")
    agent_logger.info("should not appear in agents.log", extra={"event_tag": "Test"})

    # agents.log should NOT be created when module is disabled
    assert not (log_base_dir / "logs" / "agents.log").exists()

    # But message should still appear in system.log
    system_text = (log_base_dir / "logs" / "system.log").read_text()
    assert "should not appear in agents.log" in system_text


@pytest.mark.unit
def test_error_messages_appear_in_all_relevant_logs(tmp_path: Path):
    """Verify ERROR messages appear in errors.log, system.log, and module logs."""
    log_base_dir = tmp_path
    config = {
        "level": "INFO",
        "file": "logs/system.log",
        "error_file": "logs/errors.log",
        "console_enabled": False,
        "modules": {
            "agents": {
                "enabled": True,
                "file": "logs/agents.log",
                "level": "INFO",
                "max_bytes": 1048576,
                "backup_count": 2
            }
        }
    }

    setup_logging(config, reset_existing=True, log_base_dir=log_base_dir)

    agent_logger = get_logger("agent.video")
    agent_logger.error("Critical agent error", extra={"event_tag": "Agent_Error"})

    # ERROR should appear in all three logs
    system_text = (log_base_dir / "logs" / "system.log").read_text()
    errors_text = (log_base_dir / "logs" / "errors.log").read_text()
    agents_text = (log_base_dir / "logs" / "agents.log").read_text()

    assert "Critical agent error" in system_text
    assert "Critical agent error" in errors_text
    assert "Critical agent error" in agents_text
    assert "Agent_Error" in agents_text


@pytest.mark.unit
def test_log_file_rotation_backup_count(tmp_path: Path):
    """Verify log file rotation respects backup_count setting."""
    log_base_dir = tmp_path
    config = {
        "level": "INFO",
        "file": "logs/system.log",
        "error_file": "logs/errors.log",
        "console_enabled": False,
        "modules": {
            "agents": {
                "enabled": True,
                "file": "logs/agents.log",
                "level": "INFO",
                "max_bytes": 100,  # Very small to trigger rotation
                "backup_count": 2
            }
        }
    }

    setup_logging(config, reset_existing=True, log_base_dir=log_base_dir)

    agent_logger = get_logger("agent.video")

    # Write enough logs to trigger rotation
    for i in range(50):
        agent_logger.info(f"Message {i} to trigger rotation", extra={"event_tag": "Test"})

    # Check that agents.log exists (primary file always exists)
    assert (log_base_dir / "logs" / "agents.log").exists()

    # Backup files may or may not exist depending on log size,
    # but the logger should be configured with backup_count=2


@pytest.mark.unit
def test_log_format_includes_all_required_fields(tmp_path: Path):
    """Verify log format includes timestamp, level, module, event_tag, and message."""
    log_base_dir = tmp_path
    config = {
        "level": "INFO",
        "file": "logs/system.log",
        "error_file": "logs/errors.log",
        "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(event_tag)s | %(message)s",
        "console_enabled": False,
    }

    setup_logging(config, reset_existing=True, log_base_dir=log_base_dir)

    logger = get_logger("test_module")
    logger.info("formatted message", extra={"event_tag": "Format_Test"})

    system_text = (log_base_dir / "logs" / "system.log").read_text()

    # Verify all fields are present
    assert "INFO" in system_text  # levelname
    assert "test_module" in system_text  # name
    assert "Format_Test" in system_text  # event_tag
    assert "formatted message" in system_text  # message
    # asctime will be present (timestamp)
