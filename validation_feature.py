import requests

GRAPHOPPER_API_KEY = "94cc9301-76da-4df6-9912-fbf7a84a86e6"
GRAPHOPPER_URL = "https://graphhopper.com/api/1/geocode"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

def validate_city(city_name):
    """Validate city using GraphHopper API and return coordinates + name"""
    if not city_name.strip():
        return None, "City name cannot be empty."

    params = {
        "q": city_name,
        "locale": "en",
        "limit": 1,
        "key": GRAPHOPPER_API_KEY
    }
    response = requests.get(GRAPHOPPER_URL, params=params)
    if response.status_code != 200:
        return None, f"API error: {response.status_code}"

    data = response.json()
    hits = data.get("hits", [])
    if not hits:
        return None, "Invalid city name. Please try again."

    city = hits[0].get("name", "Unknown City")
    country = hits[0].get("country", "Unknown Country")
    lat = hits[0]["point"]["lat"]
    lon = hits[0]["point"]["lng"]
    return (city, country, lat, lon), None

def get_weather(lat, lon, unit="metric"):
    """Fetch weather from Open-Meteo API in metric or imperial units"""
    temp_unit = "fahrenheit" if unit == "imperial" else "celsius"
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

# ======= Main Program =======
while True:
    city_input = input("Enter a city name: ").strip()
    city_info, err = validate_city(city_input)
    if err:
        print(err)
    else:
        break

unit_choice = input("Choose units (metric/imperial): ").strip().lower()
if unit_choice not in ["metric", "imperial"]:
    print("⚠ Invalid choice, defaulting to metric.")
    unit_choice = "metric"

city, country, lat, lon = city_info
temp, err = get_weather(lat, lon, unit_choice)
if err:
    print(err)
else:
    unit_label = "°C" if unit_choice == "metric" else "°F"
    print(f"✅ City found: {city}, {country}")
    print(f"🌡 Temperature: {temp} {unit_label}")
