"""
CLI entry point for hw4_tourguide package.
Runs the full multi-agent, multi-threaded tour-guide system.
"""

import argparse
import sys
import re
from datetime import datetime
from pathlib import Path
from queue import Queue
from typing import Dict, Any, List

from hw4_tourguide import __version__
from hw4_tourguide.config_loader import ConfigLoader
from hw4_tourguide.logger import setup_logging, get_logger
from hw4_tourguide.stub_route_provider import StubRouteProvider
from hw4_tourguide.route_provider import CachedRouteProvider, GoogleMapsProvider
from hw4_tourguide.scheduler import Scheduler
from hw4_tourguide.stub_agents import VideoStubAgent, SongStubAgent, KnowledgeStubAgent
from hw4_tourguide.judge import JudgeAgent
from hw4_tourguide.orchestrator import Orchestrator
from hw4_tourguide.output_writer import OutputWriter
from hw4_tourguide.agents.video_agent import VideoAgent
from hw4_tourguide.agents.song_agent import SongAgent
from hw4_tourguide.agents.knowledge_agent import KnowledgeAgent
from hw4_tourguide.tools.youtube_client import YouTubeClient
from hw4_tourguide.tools.spotify_client import SpotifyClient
from hw4_tourguide.tools.wikipedia_client import WikipediaClient, DuckDuckGoClient
from hw4_tourguide.tools.circuit_breaker import CircuitBreaker
from hw4_tourguide.tools.metrics_collector import MetricsCollector
from hw4_tourguide.tools.llm_client import llm_factory
from hw4_tourguide.file_interface import CheckpointWriter


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hw4_tourguide",
        description="Route Enrichment Tour-Guide System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m hw4_tourguide --from "Boston, MA" --to "Cambridge, MA" --mode cached --log-level DEBUG
  python -m hw4_tourguide --from "Home" --to "Work" --mode live

Output & logs:
  - Default output path (no --output): creates per-run folder under ./output/
    named YYYY-MM-DD_HH-MM-SS_<origin>_to_<destination> with JSON/MD/CSV,
    logs, and checkpoints inside (run-specific logging).
  - Custom output: pass --output /path/to/final.json to write JSON there;
    MD/CSV and checkpoints are written under that base; logs remain in the
    configured log directory (default ./logs/).

Cached vs live:
  - cached mode: uses data/routes/*.json (demo_boston_mit.json ships with repo)
  - live mode: requires GOOGLE_MAPS_API_KEY in .env (Directions + Geocoding APIs)
        """,
    )

    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--from", dest="origin", type=str, required=True, help='Starting location (e.g., "Boston, MA")')
    parser.add_argument("--to", dest="destination", type=str, required=True, help='Destination location (e.g., "Cambridge, MA")')
    parser.add_argument(
        "--mode",
        type=str,
        choices=["live", "cached"],
        default="cached",
        help="Run mode (live uses real APIs; cached uses local data).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/settings.yaml"),
        help="Path to YAML configuration file (default: config/settings.yaml)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/final_route.json"),
        help="Path for output JSON file (default: output/final_route.json)",
    )
    return parser


def _sanitize_location_name(location: str, max_length: int = 30) -> str:
    """
    Sanitizes location name for use in directory names.
    Removes special characters, replaces spaces with underscores, and truncates.
    """
    # Remove special characters, keep only alphanumeric, spaces, and hyphens
    sanitized = re.sub(r'[^\w\s-]', '', location)
    # Replace spaces with underscores
    sanitized = re.sub(r'\s+', '_', sanitized)
    # Replace multiple underscores/hyphens with single ones
    sanitized = re.sub(r'[-_]+', '_', sanitized)
    # Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    return sanitized


def _create_run_directory_name(origin: str, destination: str) -> str:
    """
    Creates a run-specific directory name in format:
    YYYY-MM-DD_HH-MM-SS_Origin_to_Destination
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    origin_clean = _sanitize_location_name(origin)
    dest_clean = _sanitize_location_name(destination)
    return f"{timestamp}_{origin_clean}_to_{dest_clean}"


def run_pipeline(config: Dict[str, Any], args: argparse.Namespace, config_loader: ConfigLoader) -> int:
    mode = args.mode.lower()

    # 1. Determine if using run-specific directory organization
    # Ensure args.output is a Path object
    output_path = Path(args.output) if not isinstance(args.output, Path) else args.output

    # Only use run-specific directories if default output path is used
    default_output = Path("output/final_route.json")
    use_run_specific_dir = (output_path == default_output)

    if use_run_specific_dir:
        run_dir_name = _create_run_directory_name(args.origin, args.destination)
        run_base_dir = Path(config["output"].get("base_dir", "output")) / run_dir_name
        final_output_base_message = str(run_base_dir) # For logging info message
    else:
        run_base_dir = output_path.parent # This is the custom base directory
        final_output_base_message = str(output_path) # For logging info message, show the user's explicit path

    # All pipeline logic moved here
    try:
        # ALWAYS set up logging to use run_base_dir as its anchor
        # setup_logging will handle creating 'logs' subdirectory within run_base_dir
        setup_logging(config.get("logging", {}), reset_existing=True, log_base_dir=run_base_dir)
        logger = get_logger("main") # Get logger after it's been set up

        # ALWAYS update config["metrics"]["file"] to be relative to run_base_dir
        # This will put metrics.json into 'run_base_dir/logs/'
        metrics_filename = Path(config.get("metrics", {}).get("file", "logs/metrics.json")).name
        metrics_full_path = run_base_dir / "logs" / metrics_filename
        metrics_full_path.parent.mkdir(parents=True, exist_ok=True) # Ensure the logs dir exists for metrics
        config["metrics"]["file"] = str(metrics_full_path)

        if use_run_specific_dir:
            logger.info(
                f"Using run-specific directory | Path: {final_output_base_message} | Origin: {args.origin} | Destination: {args.destination}",
                extra={"event_tag": "Setup", "run_directory": str(run_base_dir)}
            )
        else:
            logger.info(
                f"Using custom output path | Main output: {final_output_base_message} | Logs/Metrics root: {run_base_dir}", # Clarify where logs/metrics go
                extra={"event_tag": "Setup"}
            )
            
        metrics = MetricsCollector( # MetricsCollector initialization needs to be here
            path=config.get("metrics", {}).get("file", "logs/metrics.json"),
            update_interval=float(config.get("metrics", {}).get("update_interval", 5.0)),
        ) if config.get("metrics", {}).get("enabled", True) else None

        checkpoint_writer = CheckpointWriter(
            base_dir=run_base_dir / "checkpoints",
            retention_days=config["output"].get("checkpoint_retention_days", 7),
        )

        # 4. Set up Route Provider
        route_provider = _select_route_provider(config, mode, config_loader, run_base_dir / "checkpoints", metrics)
        try:
            route_payload = route_provider.get_route(args.origin, args.destination)
        except FileNotFoundError:
            logger.warning(
                f"No cached route found for '{args.origin}' to '{args.destination}'. Falling back to stub provider.",
                extra={"event_tag": "Error"},
            )
            route_payload = StubRouteProvider().get_route(args.origin, args.destination)

        # 5. Initialize Scheduler
        tasks = route_payload.get("tasks", [])
        task_queue: Queue = Queue()
        scheduler = Scheduler(
            tasks=tasks,
            interval=config["scheduler"]["interval"],
            queue=task_queue,
            checkpoints_enabled=config["output"].get("checkpoints_enabled", True),
            checkpoint_dir=run_base_dir / "checkpoints",
            metrics=metrics,
        )

        # 6. Build Agents and Judge
        agents = _build_agents(config_loader, config, metrics, checkpoint_writer, mode)
        judge = JudgeAgent(
            config=config.get("judge", {}),
            logger=get_logger("judge"),
            metrics_collector=metrics,
            secrets_fn=config_loader.get_secret,
        )

        # 7. Initialize Orchestrator
        orchestrator = Orchestrator(
            queue=task_queue,
            agents=agents,
            judge=judge,
            max_workers=config["orchestrator"]["max_workers"],
            checkpoint_writer=checkpoint_writer,
            metrics=metrics,
        )

        # 8. Run pipeline
        scheduler.start()
        logger.info("Scheduler started, pipeline running...", extra={"event_tag": "Scheduler"})
        results = orchestrator.run()

        # 9. Write output and clean up
        if use_run_specific_dir:
            # Use run-specific directory structure with configurable filenames
            json_filename = Path(config["output"].get("json_file", "output/final_route.json")).name
            md_filename = Path(config["output"].get("markdown_file", "output/summary.md")).name
            csv_filename = Path(config["output"].get("csv_file", "output/tour_export.csv")).name

            output_json_path = run_base_dir / json_filename
            output_report_path = run_base_dir / md_filename
            output_csv_path = run_base_dir / csv_filename
        else:
            # Respect custom output path
            output_json_path = output_path
            output_report_path = output_path.parent / f"{output_path.stem}.md"
            output_csv_path = output_path.parent / f"{output_path.stem}.csv"

        output_writer = OutputWriter(
            json_path=output_json_path,
            report_path=output_report_path,
            csv_path=output_csv_path,
            checkpoint_writer=checkpoint_writer
        )
        output_writer.write_json(results)
        output_writer.write_report(results)
        output_writer.write_csv(results)
        
        if metrics:
            metrics.flush()
            metrics.stop()

        if use_run_specific_dir:
            logger.info(
                f"Pipeline complete | Run Directory: {run_base_dir} | "
                f"Outputs: JSON={output_json_path.name}, MD={output_report_path.name}, CSV={output_csv_path.name}",
                extra={"event_tag": "Orchestrator", "run_directory": str(run_base_dir)}
            )
        else:
            logger.info(
                f"Pipeline complete | Outputs: JSON={output_json_path}, MD={output_report_path}, CSV={output_csv_path}",
                extra={"event_tag": "Orchestrator"}
            )
        return 0
    except Exception as e: # Catch any exceptions that occur during pipeline execution
        logger.exception("An unexpected error occurred during pipeline execution.")
        return 1


def _select_route_provider(config: Dict[str, Any], mode: str, config_loader: ConfigLoader, checkpoint_dir: Path, metrics: MetricsCollector):
    if mode == "live":
        key = config_loader.get_secret("GOOGLE_MAPS_API_KEY")
        if key:
            return GoogleMapsProvider(
                api_key=key,
                retry_attempts=config["route_provider"].get("api_retry_attempts", 3),
                timeout=config["route_provider"].get("api_timeout", 10.0),
                max_steps=config["route_provider"].get("max_steps", 8),
                checkpoints_enabled=config["output"].get("checkpoints_enabled", True),
                checkpoint_dir=checkpoint_dir,
                metrics=metrics,
            )
        get_logger("route_provider.live").warning(
            "GOOGLE_MAPS_API_KEY missing; falling back to stub route provider",
            extra={"event_tag": "Error"},
        )
        return StubRouteProvider()
    
    return CachedRouteProvider(
        cache_dir=Path(config["route_provider"].get("cache_dir", "data/routes")),
        checkpoints_enabled=config["output"].get("checkpoints_enabled", True),
        checkpoint_dir=checkpoint_dir,
    )


def _build_agents(
    config_loader: ConfigLoader, 
    config: Dict[str, Any], 
    metrics: MetricsCollector, 
    writer: CheckpointWriter,
    mode: str,
) -> Dict[str, Any]:
    """
    Build agents using real clients when credentials are present; fall back to stubs otherwise.
    """
    cb_enabled = config["circuit_breaker"].get("enabled", True)
    cb_timeout = config["circuit_breaker"].get("timeout", 60.0)
    cb_fail = config["circuit_breaker"].get("failure_threshold", 5)
    
    video_cb = CircuitBreaker("youtube", failure_threshold=cb_fail, timeout=cb_timeout)
    # Song CB will be determined based on active client
    knowledge_cb = CircuitBreaker("knowledge", failure_threshold=cb_fail, timeout=cb_timeout)

    youtube_key = config_loader.get_secret("YOUTUBE_API_KEY")
    spotify_id = config_loader.get_secret("SPOTIFY_CLIENT_ID")
    spotify_secret = config_loader.get_secret("SPOTIFY_CLIENT_SECRET")
    llm_client = None
    if config["agents"].get("use_llm_for_queries"):
        try:
            llm_client = llm_factory(config["agents"], config_loader.get_secret)
        except Exception as exc:  # pragma: no cover - defensive guard
            get_logger("llm").warning(
                f"LLM client unavailable for agent queries: {exc}; using heuristics",
                extra={"event_tag": "LLM"},
            )
            llm_client = None

    # Helper to merge parent agents settings into child config
    def merge_agent_config(agent_name: str) -> dict:
        """Merge parent-level agents settings into specific agent config."""
        parent_settings = {
            "use_llm_for_queries": config["agents"].get("use_llm_for_queries", False),
            "llm_provider": config["agents"].get("llm_provider", "mock"),
            "llm_query_timeout": config["agents"].get("llm_query_timeout", 10.0),
            "llm_retries": config["agents"].get("llm_retries", 3),
            "llm_backoff": config["agents"].get("llm_backoff", "exponential"),
            "llm_max_prompt_chars": config["agents"].get("llm_max_prompt_chars", 4000),
            "llm_max_tokens": config["agents"].get("llm_max_tokens", 4000),
            "llm_fallback": config["agents"].get("llm_fallback", True),
        }
        # Merge: parent settings first, then child can override
        return {**parent_settings, **config["agents"][agent_name]}

    # Video Agent
    video_cfg = merge_agent_config("video")
    if mode == "cached" and not config["agents"].get("override_cached_agent_settings", False):
        # In cached mode, if not overridden, agents should generally mock their content retrieval.
        # However, we want to allow LLM query generation in cached mode for testing.
        # So, we only force mock_mode if use_llm_for_queries is also false.
        if not video_cfg.get("use_llm_for_queries", False):
            video_cfg["use_live"] = False
            video_cfg["mock_mode"] = True
    if youtube_key and video_cfg.get("use_live", True) and not video_cfg.get("mock_mode", False):
        video_client = YouTubeClient(api_key=youtube_key, timeout=video_cfg.get("timeout", 10.0))
        video_agent = VideoAgent(
            config=video_cfg, checkpoint_writer=writer, client=video_client,
            circuit_breaker=video_cb if cb_enabled else None, metrics=metrics, llm_client=llm_client,
        )
    else:
        video_agent = VideoStubAgent()

    # Song Agent
    song_cfg = merge_agent_config("song")
    if mode == "cached" and not config["agents"].get("override_cached_agent_settings", False):
        if not song_cfg.get("use_llm_for_queries", False):
            song_cfg["use_live"] = False
            song_cfg["mock_mode"] = True
            song_cfg["use_youtube_secondary"] = False
    song_client, secondary_song_client = None, None

    if spotify_id and spotify_secret and song_cfg.get("use_live", True) and not song_cfg.get("mock_mode", False):
        song_client = SpotifyClient(
            client_id=spotify_id, client_secret=spotify_secret, timeout=song_cfg.get("timeout", 10.0)
        )
    
    if youtube_key and song_cfg.get("use_youtube_secondary", True) and not song_cfg.get("mock_mode", False):
        yt_client = YouTubeClient(api_key=youtube_key, timeout=song_cfg.get("timeout", 10.0))
        
        class _YouTubeSongAdapter:
            def search_tracks(self, query: str, limit: int) -> List[Dict[str, Any]]:
                vids = yt_client.search_videos(f"{query} song", limit)
                return [{"id": v["id"], "title": v["title"], "artist": v.get("channel"), "url": v["url"], "source": "youtube"} for v in vids]
            def fetch_track(self, track_id: str) -> Dict[str, Any]:
                v = yt_client.fetch_video(track_id)
                return {"id": v["id"], "title": v["title"], "artist": v.get("channel"), "url": v["url"], "source": "youtube"}

        secondary_song_client = _YouTubeSongAdapter()

    if song_client or secondary_song_client:
        # Determine appropriate circuit breaker
        if song_client:
            current_song_cb = CircuitBreaker("spotify", failure_threshold=cb_fail, timeout=cb_timeout)
        elif secondary_song_client:
            # If falling back to YouTube, share the YouTube circuit breaker
            current_song_cb = video_cb
        else:
            current_song_cb = None

        song_agent = SongAgent(
            config=song_cfg, checkpoint_writer=writer, client=song_client, secondary_client=secondary_song_client,
            circuit_breaker=current_song_cb if cb_enabled else None, metrics=metrics, llm_client=llm_client,
        )
    else:
        song_agent = SongStubAgent()

    # Knowledge Agent
    knowledge_cfg = merge_agent_config("knowledge")
    if mode == "cached" and not config["agents"].get("override_cached_agent_settings", False):
        if not knowledge_cfg.get("use_llm_for_queries", False):
            knowledge_cfg["use_live"] = False
            knowledge_cfg["mock_mode"] = True
    if knowledge_cfg.get("use_live", True) and not knowledge_cfg.get("mock_mode", False):
        knowledge_agent = KnowledgeAgent(
            config=knowledge_cfg, checkpoint_writer=writer,
            client=WikipediaClient(timeout=knowledge_cfg.get("timeout", 10.0)),
            secondary_client=DuckDuckGoClient(timeout=knowledge_cfg.get("timeout", 10.0)),
            circuit_breaker=knowledge_cb if cb_enabled else None, metrics=metrics, llm_client=llm_client,
        )
    else:
        knowledge_agent = KnowledgeStubAgent()

    return {"video": video_agent, "song": song_agent, "knowledge": knowledge_agent}


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    try:
        # Early determination of run_base_dir for consistent logging from the start
        config_loader = ConfigLoader(config_path=args.config, cli_overrides={"logging.level": args.log_level})
        config = config_loader.get_all() # Load config first to get output settings

        # 1. Determine if using run-specific directory organization
        output_path = Path(args.output) if not isinstance(args.output, Path) else args.output
        default_output = Path("output/final_route.json")
        use_run_specific_dir = (output_path == default_output)

        if use_run_specific_dir:
            run_dir_name = _create_run_directory_name(args.origin, args.destination)
            run_base_dir = Path(config["output"].get("base_dir", "output")) / run_dir_name
        else:
            run_base_dir = output_path.parent

        # Only setup logging once, with the correct run_base_dir
        setup_logging(config.get("logging", {}), reset_existing=True, log_base_dir=run_base_dir if use_run_specific_dir else None)
        logger = get_logger("main") # Get logger after it's been set up

        # Now print the initial info message about the run directory
        if use_run_specific_dir:
            logger.info(
                f"Using run-specific directory | Path: {run_base_dir} | Origin: {args.origin} | Destination: {args.destination}",
                extra={"event_tag": "Setup", "run_directory": str(run_base_dir)}
            )
        else:
            logger.info(
                f"Using custom output path | Path: {output_path}",
                extra={"event_tag": "Setup"}
            )
            
        return run_pipeline(config, args, config_loader)
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found at '{args.config}'", file=sys.stderr)
        return 1
    except Exception as e:
        # Fallback for when logger fails or other unexpected error
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
