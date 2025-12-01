import argparse
import re
from datetime import datetime
from pathlib import Path
import sys

# Ensure hw4_tourguide is in path to import ConfigLoader
# This is a bit hacky but ensures the script can be run standalone
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))

from hw4_tourguide.config_loader import ConfigLoader

def check_scheduler_interval(log_file_path: Path, config_file_path: Path = Path("config/settings.yaml")):
    """
    Checks the scheduler's emission intervals against the configured interval.

    Args:
        log_file_path: Path to the system log file.
        config_file_path: Path to the main configuration file.
    """
    print(f"--- Checking Scheduler Intervals ---")
    print(f"Log file: {log_file_path}")
    print(f"Config file: {config_file_path}")

    if not log_file_path.exists():
        print(f"Error: Log file not found at {log_file_path}")
        sys.exit(1)
    
    # Load scheduler interval from config
    config_loader = ConfigLoader(config_path=config_file_path)
    expected_interval = config_loader.get("scheduler.interval")
    
    if expected_interval is None:
        print(f"Error: 'scheduler.interval' not found in config file {config_file_path}.")
        print(f"Please ensure it is defined. Defaulting to 2.0s for checks.")
        expected_interval = 2.0 # Fallback default
    
    tolerance = 0.2 # seconds
    
    print(f"Expected interval: {expected_interval:.1f}s (Tolerance: +/-{tolerance:.1f}s)")

    # Regex to capture timestamp and step number for scheduler EMIT events
    # Example: 2025-12-01 16:10:36,155 | INFO | hw4_tourguide.scheduler | Scheduler_Emit | Scheduler_Emit | Step 1/4: Boston Common | ...
    log_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) \| .*?Step (\d+)/\d+:.*")
    
    timestamps = []
    
    with open(log_file_path, 'r') as f:
        for line in f:
            match = log_pattern.match(line)
            if match:
                timestamp_str = match.group(1)
                step_number = int(match.group(2))
                # Parse timestamp - format is 'YYYY-MM-DD HH:MM:SS,ms'
                # Python's datetime doesn't directly support %f for milliseconds if comma separated, so replace
                # It expects microseconds for %f, so we'll convert ms to micro
                try:
                    dt_object = datetime.strptime(timestamp_str.replace(',', '.'), '%Y-%m-%d %H:%M:%S.%f')
                    timestamps.append((step_number, dt_object))
                except ValueError as e:
                    print(f"Warning: Could not parse timestamp '{timestamp_str}': {e} in line: {line.strip()}")

    if not timestamps:
        print("No 'Scheduler | EMIT' events found in the log file.")
        sys.exit(0)

    # Sort timestamps by step number to handle out-of-order logs, though scheduler is sequential
    timestamps.sort()

    previous_time = None
    all_within_tolerance = True
    
    print(f"\n--- Analysis ---")
    for i, (step, current_time) in enumerate(timestamps):
        if previous_time:
            interval_diff = (current_time - previous_time).total_seconds()
            
            # Check deviation
            if not (expected_interval - tolerance <= interval_diff <= expected_interval + tolerance):
                print(f"Step {timestamps[i-1][0]} to {step}: Interval {interval_diff:.3f}s "
                      f"(Expected: {expected_interval:.1f}s +/-{tolerance:.1f}s) -> OUT OF TOLERANCE")
                all_within_tolerance = False
            # else:
            #     print(f"Step {timestamps[i-1][0]} to {step}: Interval {interval_diff:.3f}s -> OK") # Too verbose
        previous_time = current_time

    print(f"\n--- Result ---")
    if all_within_tolerance:
        print(f"All scheduler intervals are within {expected_interval:.1f}s +/-{tolerance:.1f}s.")
        sys.exit(0)
    else:
        print(f"Some scheduler intervals were OUT OF TOLERANCE.")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check scheduler emission intervals in system logs.")
    parser.add_argument("log_file", type=str, help="Path to the system log file (e.g., logs/system.log)")
    parser.add_argument("--config", type=str, default="config/settings.yaml",
                        help="Path to the main configuration file.")
    
    args = parser.parse_args()
    
    check_scheduler_interval(Path(args.log_file), Path(args.config))
