"""
Route providers (Mission M7.1).

Provides abstractions for fetching routes from Google Maps (live) or cached files.
Emits task lists ready for the Scheduler (one dict per step) and writes checkpoints
per ADR-009. No extra API calls are made; only lightweight cleaning/formatting.
"""

import json
import uuid
import time
import hashlib
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from importlib import resources

import requests

from hw4_tourguide.logger import get_logger


class RouteProvider(ABC):
    @abstractmethod
    def get_route(self, origin: str, destination: str) -> Dict[str, Any]:
        """
        Return a payload containing task list and metadata.

        Returns:
            {
                "tasks": [task_dict, ...],  # ready for scheduler queue
                "metadata": {origin, destination, distance, duration, transaction_id, route_context, timestamp}
            }
        }
        """


class GoogleMapsProvider(RouteProvider):
    def __init__(
        self,
        api_key: str,
        retry_attempts: int = 3,
        timeout: float = 10.0,
        max_steps: int = 8,
        checkpoints_enabled: bool = True,
        checkpoint_dir: Path = Path("output/checkpoints"),
        circuit_breaker: Optional[Any] = None,
        metrics: Optional[Any] = None,
    ):
        self.api_key = api_key
        self.retry_attempts = retry_attempts
        self.timeout = timeout
        self.max_steps = max_steps
        self.checkpoints_enabled = checkpoints_enabled
        self.checkpoint_dir = checkpoint_dir
        self.circuit_breaker = circuit_breaker
        self.metrics = metrics
        self.logger = get_logger("route_provider.live")
        # Cache for geocoding results to avoid duplicate API calls
        self._geocoding_cache: Dict[str, Dict[str, str]] = {}

        # Log provider initialization
        self.logger.info(
            f"RouteProvider_Init | Provider: GoogleMaps | Max Steps: {self.max_steps} | "
            f"Checkpoints: {'enabled' if self.checkpoints_enabled else 'disabled'}",
            extra={"event_tag": "RouteProvider_Init", "max_steps": self.max_steps}
        )
        self.logger.debug(f"DEBUG: GoogleMapsProvider initialized with checkpoint_dir: {self.checkpoint_dir}")


    def get_route(self, origin: str, destination: str) -> Dict[str, Any]:
        route_start = time.time()
        tid = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"

        self.logger.info(
            f"RouteProvider_Request | TID: {tid} | Origin: \"{origin}\" | Destination: \"{destination}\"",
            extra={"event_tag": "RouteProvider_Request", "transaction_id": tid}
        )

        if not self.api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY is required for live mode")

        params = {
            "origin": origin,
            "destination": destination,
            "mode": "driving",
            "key": self.api_key,
        }

        response_data = None

        self.logger.info(
            f"RouteProvider_API_Directions | TID: {tid} | Calling Google Maps Directions API",
            extra={"event_tag": "RouteProvider_API_Directions", "transaction_id": tid}
        )

        api_start = time.time()
        for attempt in range(1, self.retry_attempts + 1):
            try:
                resp = self._call_with_breaker(
                    lambda: requests.get(
                        "https://maps.googleapis.com/maps/api/directions/json",
                        params=params,
                        timeout=self.timeout,
                    )
                )
                resp.raise_for_status()
                response_data = resp.json()
                if response_data.get("status") == "OK":
                    api_time_ms = (time.time() - api_start) * 1000
                    self.logger.info(
                        f"RouteProvider_API_Response | TID: {tid} | Status: {response_data.get('status')} | "
                        f"Time: {api_time_ms:.0f}ms",
                        extra={"event_tag": "RouteProvider_API_Response", "transaction_id": tid, "api_status": response_data.get('status')}
                    )
                    self._record_metrics(success=True)
                    break
                self.logger.warning(
                    f"Google Maps status {response_data.get('status')} on attempt {attempt}",
                    extra={"event_tag": "API_Call"},
                )
            except Exception as exc:
                self.logger.warning(
                    f"Google Maps call failed (attempt {attempt}): {exc}",
                    extra={"event_tag": "Error"},
                )
                self._record_metrics(success=False)
                time.sleep(2 ** (attempt - 1))

        if not response_data or response_data.get("status") != "OK":
            self.logger.error(
                f"RouteProvider_Error | TID: {tid} | Failed after {self.retry_attempts} attempts",
                extra={"event_tag": "RouteProvider_Error", "transaction_id": tid}
            )
            raise RuntimeError("Failed to fetch route from Google Maps after retries")

        payload = self._convert_response(response_data, origin, destination, tid, route_start)
        self._write_checkpoint(payload, "00_route.json")
        return payload

    def _reverse_geocode(self, lat: float, lng: float) -> Dict[str, str]:
        """
        Reverse geocode coordinates to get address and location name.
        Uses caching to avoid duplicate API calls for same coordinates.

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            Dict with 'location_name' and 'address' keys
        """
        # Round coordinates to 6 decimal places for cache key (precision ~0.1m)
        cache_key = f"{lat:.6f},{lng:.6f}"

        # Check cache first
        if cache_key in self._geocoding_cache:
            return self._geocoding_cache[cache_key]

        try:
            params = {
                "latlng": f"{lat},{lng}",
                "key": self.api_key,
            }

            resp = requests.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params=params,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            geocode_data = resp.json()

            if geocode_data.get("status") == "OK" and len(geocode_data.get("results", [])) > 0:
                result = geocode_data["results"][0]
                formatted_address = result.get("formatted_address", "")

                # Extract location name from first address component or formatted address
                location_name = formatted_address.split(",")[0] if formatted_address else f"{lat:.6f},{lng:.6f}"

                # Try to get a better location name from address components
                for component in result.get("address_components", []):
                    types = component.get("types", [])
                    # Prefer: intersection > route > neighborhood > locality
                    if "intersection" in types or "point_of_interest" in types:
                        location_name = component.get("long_name", location_name)
                        break
                    elif "route" in types and location_name == formatted_address.split(",")[0]:
                        location_name = component.get("long_name", location_name)

                result_dict = {
                    "location_name": location_name,
                    "address": formatted_address
                }

                # Cache the result
                self._geocoding_cache[cache_key] = result_dict
                self.logger.debug(f"Geocoded {cache_key} -> {location_name}", extra={"event_tag": "API_Call"})

                return result_dict
            else:
                self.logger.warning(
                    f"Geocoding failed for {cache_key}: {geocode_data.get('status')}",
                    extra={"event_tag": "API_Call"}
                )

        except Exception as exc:
            self.logger.warning(
                f"Geocoding API error for {cache_key}: {exc}",
                extra={"event_tag": "Error"}
            )

        # Fallback: return coordinate-based name
        return {
            "location_name": f"{lat:.6f},{lng:.6f}",
            "address": None
        }

    def _extract_street_name_fallback(self, html_instructions: str) -> str:
        """
        Extract street name from HTML instructions as fallback.

        Args:
            html_instructions: HTML instruction string from Google Maps

        Returns:
            Extracted street name or cleaned instruction
        """
        # Strip HTML tags
        text = re.sub(r'<[^<]+?>', '', html_instructions)

        # Try to extract street name patterns
        patterns = [
            r'on\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Way|Pkwy|Parkway))',
            r'onto\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Way|Pkwy|Parkway))',
            r'toward\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Way|Pkwy|Parkway))',
            r'at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Dr|Drive|Ln|Lane|Way|Pkwy|Parkway))',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        # If no street name found, return cleaned instruction
        return text

    def _convert_response(self, data: Dict[str, Any], origin: str, destination: str, tid: str, route_start: float) -> Dict[str, Any]:
        def _strip_html(text: Optional[str]) -> str:
            if not text:
                return ""
            return re.sub("<[^<]+?>", "", text)

        route_context = destination or origin
        route_timestamp = time.time()
        routes = data.get("routes") or []
        if not routes or not routes[0].get("legs"):
            raise ValueError("Invalid Google Maps response: missing legs")
        legs = routes[0]["legs"][0]

        steps = legs.get("steps", [])
        num_steps = len(steps)

        # Validate route step count against configured maximum
        if num_steps > self.max_steps:
            self.logger.error(
                f"Route has {num_steps} steps, exceeds maximum of {self.max_steps}",
                extra={"event_tag": "Route_Validation"}
            )
            raise ValueError(
                f"Route validation failed: This route has {num_steps} steps, which exceeds "
                f"the configured maximum of {self.max_steps} steps.\n\n"
                f"This limit exists to manage API quotas and costs:\n"
                f"  - YouTube API quota: {num_steps} steps would use ~{num_steps * 303} quota units "
                f"(daily free limit: 10,000 units)\n"
                f"  - Execution time: ~{num_steps * 0.6:.1f} minutes\n\n"
                f"Please choose a shorter route with ≤{self.max_steps} steps.\n"
                f"Hint: Try selecting closer destinations or using intermediate waypoints."
            )

        self.logger.info(
            f"Converting route with {num_steps} steps, using reverse geocoding",
            extra={"event_tag": "Route_Processing"}
        )

        tasks: List[Dict[str, Any]] = []
        for idx, step in enumerate(legs.get("steps", []), start=1):
            instructions = _strip_html(step.get("html_instructions")) or ""
            lat = step.get("end_location", {}).get("lat")
            lng = step.get("end_location", {}).get("lng")

            # Use reverse geocoding to get high-quality address and location name
            geocoded = self._reverse_geocode(lat, lng)
            location_name = geocoded["location_name"]
            address = geocoded["address"]

            # If geocoding failed (address is None), use fallback extraction
            if address is None:
                self.logger.debug(
                    f"Geocoding failed for step {idx}, using fallback",
                    extra={"event_tag": "Route_Processing"}
                )
                location_name = self._extract_street_name_fallback(step.get("html_instructions", ""))
                address = None

            tasks.append(
                {
                    "transaction_id": tid,
                    "step_number": idx,
                    "location_name": location_name,
                    "coordinates": {
                        "lat": lat,
                        "lng": lng,
                    },
                    "instructions": instructions,
                    "timestamp": route_timestamp,
                    "address": address,
                    "search_hint": f"{location_name}, {route_context}" if route_context else location_name,
                    "route_context": route_context,
                }
            )

        metadata = {
            "origin": origin,
            "destination": destination,
            "distance": legs.get("distance", {}).get("text"),
            "duration": legs.get("duration", {}).get("text"),
            "transaction_id": tid,
            "route_context": route_context,
            "timestamp": route_timestamp,
        }

        # Log successful route creation
        total_time_ms = (time.time() - route_start) * 1000
        self.logger.info(
            f"RouteProvider_Success | TID: {tid} | Steps: {len(tasks)} | "
            f"Distance: {metadata.get('distance')} | Duration: {metadata.get('duration')} | "
            f"Total Time: {total_time_ms:.0f}ms",
            extra={"event_tag": "RouteProvider_Success", "transaction_id": tid, "step_count": len(tasks)}
        )

        return {"tasks": tasks, "metadata": metadata}

    def _write_checkpoint(self, payload: Dict[str, Any], filename: str) -> None:
        if not self.checkpoints_enabled:
            return
        tid = payload.get("metadata", {}).get("transaction_id", "unknown_tid")
        path = self.checkpoint_dir / tid / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2))
        self.logger.info(f"Wrote checkpoint {path}", extra={"event_tag": "Checkpoint"})

    def _call_with_breaker(self, func):
        if self.circuit_breaker:
            return self.circuit_breaker.call(func)
        return func()

    def _record_metrics(self, success: bool) -> None:
        if not self.metrics:
            return
        try:
            if success:
                self.metrics.increment_counter("api_calls.google_maps_success")
            else:
                self.metrics.increment_counter("api_calls.google_maps_failure")
        except Exception:
            # Metrics failure should not break route fetching
            pass


class CachedRouteProvider(RouteProvider):
    def __init__(
        self,
        cache_dir: Path = Path("data/routes"),
        checkpoints_enabled: bool = True,
        checkpoint_dir: Path = Path("output/checkpoints"),
        route_file: Optional[Path] = None,
    ):
        self.cache_dir = cache_dir
        self.route_file = route_file
        self.checkpoints_enabled = checkpoints_enabled
        self.checkpoint_dir = checkpoint_dir
        self.logger = get_logger("route_provider.cached")
        self.logger.debug(f"DEBUG: CachedRouteProvider initialized with checkpoint_dir: {self.checkpoint_dir}")


    def get_route(self, origin: str, destination: str) -> Dict[str, Any]:
        path = self._select_file(origin, destination)
        if not path.exists():
            raise FileNotFoundError(f"Cached route file not found: {path}")

        try:
            route_doc = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise ValueError(f"Cached route file is not valid JSON: {path}") from exc

        tasks, metadata = self._to_tasks(route_doc, origin, destination)
        payload = {"tasks": tasks, "metadata": metadata}
        self._write_checkpoint(payload, "00_route.json")
        return payload

    def _select_file(self, origin: str, destination: str) -> Path:
        if self.route_file:
            return self.route_file
        
        slug = hashlib.sha1(f"{origin}-{destination}".encode()).hexdigest()[:12]
        filename = f"{slug}.json"

        # 1. Try local cache directory
        if self.cache_dir.exists():
            candidate = self.cache_dir / filename
            if candidate.exists():
                return candidate
            # Fallback to any json in local dir
            for f in self.cache_dir.glob("*.json"):
                return f

        # 2. Try packaged data resources
        try:
            # Access the directory resource
            # Note: 'hw4_tourguide.data.routes' must be a valid package
            with resources.path("hw4_tourguide.data.routes", filename) as packaged_path:
                if packaged_path.exists():
                    self.logger.info(f"Using packaged route file: {packaged_path}")
                    return packaged_path
        except Exception:
            # If specific file not found, try to find ANY json in package (fallback)
            try:
                for resource in resources.files("hw4_tourguide.data.routes").iterdir():
                    if resource.name.endswith(".json"):
                        with resources.path("hw4_tourguide.data.routes", resource.name) as p:
                            self.logger.info(f"Using packaged fallback route: {p}")
                            return p
            except Exception:
                pass

        raise FileNotFoundError(f"No cached route files found in {self.cache_dir} or package resources")

    def _write_checkpoint(self, payload: Dict[str, Any], filename: str) -> None:
        if not self.checkpoints_enabled:
            return
        tid = payload.get("metadata", {}).get("transaction_id", "unknown_tid")
        path = self.checkpoint_dir / tid / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2))
        self.logger.info(f"Wrote checkpoint {path}", extra={"event_tag": "Config"}) # DEBUG: Check this line

    def _to_tasks(self, route_doc: Dict[str, Any], origin: str, destination: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        route_context = route_doc.get("route_context") or destination or origin
        tid = route_doc.get("transaction_id") or route_doc.get("metadata", {}).get("transaction_id") or f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
        route_timestamp = route_doc.get("timestamp") or route_doc.get("metadata", {}).get("timestamp") or time.time()
        steps = route_doc.get("tasks") or route_doc.get("steps") or []
        tasks: List[Dict[str, Any]] = []
        for step in steps:
            tasks.append(
                {
                    "transaction_id": step.get("transaction_id", tid),
                    "step_number": step.get("step_number"),
                    "location_name": step.get("location_name"),
                    "coordinates": step.get("coordinates"),
                    "instructions": step.get("instructions"),
                    "timestamp": step.get("timestamp", route_timestamp),
                    "address": step.get("address"),
                    "search_hint": step.get("search_hint") or (f"{step.get('location_name')}, {route_context}" if route_context else step.get("location_name")),
                    "route_context": route_context,
                }
            )
        metadata = {
            "origin": route_doc.get("metadata", {}).get("origin") or origin,
            "destination": route_doc.get("metadata", {}).get("destination") or destination,
            "distance": route_doc.get("metadata", {}).get("distance"),
            "duration": route_doc.get("metadata", {}).get("duration"),
            "transaction_id": tid,
            "route_context": route_context,
            "timestamp": route_timestamp,
        }
        return tasks, metadata