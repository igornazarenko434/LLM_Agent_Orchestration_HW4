import pandas as pd
import re
from datetime import datetime
from pathlib import Path

def parse_system_log(filepath):
    events = []
    # Regex: Note the spaces around pipes are \s+\| and \|
    # We need to be flexible with spaces around the pipes
    log_pattern = re.compile(r'^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+\|\s+(?P<level>\w+)\s+\|\s+(?P<module>[\w\.]+)\s+\|\s+(?P<event_tag>\w+)\s+\|\s+(?P<message>.*)')
    
    failed_count = 0
    with open(filepath, 'r') as f:
        for line in f:
            match = log_pattern.search(line)
            if match:
                try:
                    dt = datetime.strptime(match.group('timestamp'), '%Y-%m-%d %H:%M:%S,%f')
                    events.append({'message': match.group('message')})
                except ValueError: continue
            else:
                # Check if this is a line we care about (RouteProvider)
                if "RouteProvider" in line and failed_count < 5:
                    print(f"FAILED MATCH: {line.strip()}")
                    failed_count += 1
    return pd.DataFrame(events)

log_path = 'output/study_live/logs/system.log'
if Path(log_path).exists():
    print("Parsing log...")
    df = parse_system_log(log_path)
    print(f"Log loaded: {len(df)} rows")
    
    count = len(df[df['message'].str.contains('RouteProvider_API_')])
    print(f"Matches for 'RouteProvider_API_': {count}")
    
    print("\nFirst 5 messages:")
    print(df['message'].head(5).to_list())
else:
    print("Log file not found!")