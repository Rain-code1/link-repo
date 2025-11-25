import os
import sys

# Ensure the project root (where logic.py lives) is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import logic

# -----------------------------
# Tests for estimate_fuel
# -----------------------------

def test_estimate_fuel_valid():
    """
    100 km at 8 L/100km should use exactly 8L.
    """
    result = logic.estimate_fuel(100, 8)
    assert result == 8


def test_estimate_fuel_invalid_l_per_100():
    """
    If the L/100km value is not a number, function should return None
    instead of raising an error.
    """
    result = logic.estimate_fuel(50, "not-a-number")
    assert result is None


# -----------------------------
# Tests for geocode
# -----------------------------

def test_geocode_empty_location():
    """
    Empty location should not call the API and should return an error message.
    """
    coords, error = logic.geocode("")
    assert coords is None
    assert error is not None
    assert "cannot be empty" in error.lower()


def test_geocode_api_error(monkeypatch):
    """
    Simulate an API error (like 500 or timeout) and verify that geocode()
    handles it by returning a clear error message instead of crashing.
    """

    class DummyResponse:
        def raise_for_status(self):
            # Simulate what requests would do on HTTP error
            raise logic.requests.RequestException("Server error")

    def fake_get(*args, **kwargs):
        return DummyResponse()

    # Replace requests.get with our fake one
    monkeypatch.setattr(logic.requests, "get", fake_get)

    coords, error = logic.geocode("Manila")
    assert coords is None
    assert error is not None
    assert "api error" in error.lower()


# -----------------------------
# Tests for call_route (mocked)
# -----------------------------

def test_call_route_success(monkeypatch):
    """
    Simulate a successful GraphHopper routing API response.
    This avoids real network calls in CI.
    """

    fake_data = {
        "paths": [
            {
                "distance": 10000,  # meters
                "time": 600000,     # ms
                "points": "}_ilA~kbqU??",
                "instructions": [
                    {"text": "Head north", "distance": 5000},
                    {"text": "Turn right", "distance": 5000},
                ],
            }
        ]
    }

    class DummyResponse:
        def __init__(self, data):
            self._data = data

        def raise_for_status(self):
            pass

        def json(self):
            return self._data

    def fake_get(*args, **kwargs):
        return DummyResponse(fake_data)

    # Monkeypatch requests.get used inside logic.call_route
    monkeypatch.setattr(logic.requests, "get", fake_get)

    result = logic.call_route(14.6, 120.98, 14.7, 121.0, "car")

    assert "paths" in result
    assert len(result["paths"]) == 1
    assert result["paths"][0]["distance"] == 10000
    assert result["paths"][0]["time"] == 600000


# -----------------------------
# Extra tests for bike/foot modes
# -----------------------------

def _capture_request(monkeypatch):
    """
    Helper to capture the URL and params passed to requests.get
    inside logic.call_route, so we can verify the vehicle type.
    """
    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured["url"] = url
        captured["params"] = params or []
        captured["timeout"] = timeout

        class FakeResp:
            def raise_for_status(self):
                pass

            def json(self):
                # Minimal valid response for our purposes
                return {"paths": []}

        return FakeResp()

    monkeypatch.setattr(logic.requests, "get", fake_get)
    return captured


def test_call_route_uses_bike_vehicle(monkeypatch):
    """
    Ensure that when vehicle='bike', we actually send ?vehicle=bike
    to the GraphHopper API.
    """
    captured = _capture_request(monkeypatch)

    logic.call_route(14.0, 121.0, 14.5, 121.1, "bike", avoid_tolls=False)

    vehicles = [v for (k, v) in captured["params"] if k == "vehicle"]
    assert vehicles == ["bike"]


def test_call_route_uses_foot_vehicle(monkeypatch):
    """
    Ensure that when vehicle='foot', we actually send ?vehicle=foot
    to the GraphHopper API.
    """
    captured = _capture_request(monkeypatch)

    logic.call_route(14.0, 121.0, 14.5, 121.1, "foot", avoid_tolls=False)

    vehicles = [v for (k, v) in captured["params"] if k == "vehicle"]
    assert vehicles == ["foot"]
