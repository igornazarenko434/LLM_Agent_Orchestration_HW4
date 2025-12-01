"""
hw4_tourguide - Route Enrichment Tour-Guide System

A multi-agent orchestration platform that enriches Google Maps routes with
curated video, music, and knowledge content.

This package implements:
- Scheduler: Dedicated thread emitting route steps at configured intervals
- Orchestrator: ThreadPoolExecutor coordinating worker threads
- Agents: Video, Song, and Knowledge content enrichment
- Judge: Scoring agent outputs with heuristics and optional LLM
- Output Writer: JSON/Markdown/CSV exports for different personas
"""

__version__ = "0.1.0"

# Export key components for easy import
__all__ = [
    "__version__",
]
__author__ = "Route Enrichment Team"
__description__ = "Multi-agent orchestration platform for enriching driving routes with curated content"
__package_name__ = "hw4_tourguide"

# Version info
VERSION = __version__

# Package metadata
__all__ = [
    "__version__",
    "VERSION",
]
