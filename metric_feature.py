import requests

# API keys
GRAPHOPPER_API_KEY = "94cc9301-76da-4df6-9912-fbf7a84a86e6"  # Replace with your GraphHopper API key
GRAPHOPPER_URL = "https://graphhopper.com/api/1/geocode"

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def validate_city(city_name):
    """Validate city using GraphHopper API and return coordinates + name"""
    params = {
        "q": city_name,
        "locale": "en",
        "limit": 1,
        "key": GRAPHOPPER_API_KEY
    }

    response = requests.get(GRAPHOPPER_URL, params=params)

    if response.status_code != 200:
        return None, None, f"Error: {response.status_code}"

    data = response.json()
    hits = data.get("hits", [])

    if not hits:
        return None, None, "Invalid city name. Please try again."

    city = hits[0].get("name", "Unknown City")
    country = hits[0].get("country", "Unknown Country")
    lat = hits[0]["point"]["lat"]
    lon = hits[0]["point"]["lng"]

    return (city, country, lat, lon), None, None


def get_weather(lat, lon, unit="metric"):
    """Fetch weather from Open-Meteo API in metric or imperial units"""
    # Map units to Open-Meteo format
    if unit == "imperial":
        temp_unit = "fahrenheit"
    else:
        temp_unit = "celsius"

    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "temperature_unit": temp_unit
    }

    response = requests.get(OPEN_METEO_URL, params=params)

    if response.status_code != 200:
        return None, f"Weather API error: {response.status_code}"

    data = response.json()
    if "current_weather" not in data:
        return None, "No weather data available."

    temp = data["current_weather"]["temperature"]
    return temp, None


# ======================
# Main Program
# ======================
city_input = input("Enter a city name: ")
unit_choice = input("Choose units (metric/imperial): ").strip().lower()

if unit_choice not in ["metric", "imperial"]:
    print("⚠ Invalid choice, defaulting to metric.")
    unit_choice = "metric"

(city_info, err1, err2) = validate_city(city_input)

if err1 or err2:
    print(err1 or err2)
else:
    city, country, lat, lon = city_info
    temp, err3 = get_weather(lat, lon, unit_choice)

    if err3:
        print(err3)
    else:
        unit_label = "°C" if unit_choice == "metric" else "°F"
        print(f"✅ City found: {city}, {country}")
        print(f"🌡 Temperature: {temp} {unit_label}")
