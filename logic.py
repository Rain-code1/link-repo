# logic.py
"""
Core non-GUI logic for the Link route application.

This file is used by automated tests so that we do not need to
import any GUI-related modules (PySide6) in the CI environment.
"""

import json
import requests

# You can keep the same API key, but for tests we mock requests,
# so the actual value is not used.
API_KEY = "2e2cf02b-63b2-456a-a2d1-e1d04d28d6d1"
GRAPH_HOPPER_GEOCODE_URL = "https://graphhopper.com/api/1/geocode"
GRAPH_HOPPER_ROUTE_URL = "https://graphhopper.com/api/1/route"


def geocode(location_name: str):
    """Validate location using GraphHopper API and return coordinates or an error."""
    if not location_name.strip():
        return None, "Location name cannot be empty."

    params = {
        "q": location_name,
        "locale": "en",
        "limit": 1,
        "key": API_KEY,
    }

    try:
        response = requests.get(GRAPH_HOPPER_GEOCODE_URL, params=params, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        return None, f"API error: {e}"

    data = response.json()
    hits = data.get("hits", [])
    if not hits:
        return None, f"Invalid location: '{location_name}'. Please try again."

    point = hits[0]["point"]
    return (point["lat"], point["lng"]), None


def call_route(start_lat, start_lng, end_lat, end_lng, vehicle, avoid_tolls=False):
    """
    Call the GraphHopper Routing API to get a route between two points.
    Returns the parsed JSON response, or {} on error.
    """
    params = [
        ("point", f"{start_lat},{start_lng}"),
        ("point", f"{end_lat},{end_lng}"),
        ("vehicle", vehicle),
        ("locale", "en"),
        ("points_encoded", "true"),
        ("key", API_KEY),
    ]

    if avoid_tolls:
        params.append(("ch.disable", "true"))
        custom_model = {
            "priority": [
                {
                    "if": "toll == ALL",
                    "multiply_by": 0.1,
                }
            ]
        }
        params.append(("custom_model", json.dumps(custom_model)))

    try:
        r = requests.get(GRAPH_HOPPER_ROUTE_URL, params=params, timeout=45)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        # In tests we don't care about printing, just return {}
        return {}


def estimate_fuel(distance_km: float, l_per_100: float):
    """
    Calculates the estimated fuel needed for a given distance and fuel economy.
    Returns float or None if input is invalid.
    """
    try:
        return (distance_km * float(l_per_100)) / 100.0
    except (ValueError, TypeError):
        return None
