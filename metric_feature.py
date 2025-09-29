import requests

def get_weather(api_key, city, unit_system="metric"):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    units = "metric" if unit_system == "metric" else "imperial"

    params = {
        "q": city,
        "appid": api_key,
        "units": units
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        main = data["main"]
        weather = data["weather"][0]
        temp_unit = "°C" if unit_system == "metric" else "°F"

        print(f"Weather in {city}: {weather['description']}")
        print(f"Temperature: {main['temp']}{temp_unit}")
        print(f"Humidity: {main['humidity']}%")
        print(f"Pressure: {main['pressure']} hPa")
    else:
        print("City not found or error occurred.")

if __name__ == "__main__":
    api_key = "your_api_key_here"
    city = input("Enter city: ")

    unit_choice = input("Choose units (metric/imperial): ").strip().lower()
    if unit_choice not in ["metric", "imperial"]:
        print("Invalid choice, defaulting to metric.")
        unit_choice = "metric"

    get_weather(api_key, city, unit_choice)
