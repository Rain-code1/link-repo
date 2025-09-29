import requests

def get_weather(api_key, city):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        main = data["main"]
        weather = data["weather"][0]

        print(f"Weather in {city}: {weather['description']}")
        print(f"Temperature: {main['temp']}°C")
        print(f"Humidity: {main['humidity']}%")
        print(f"Pressure: {main['pressure']} hPa")
    else:
        print("City not found or error occurred.")

if __name__ == "__main__":
    api_key = "your_api_key_here"
    
    while True:
        city = input("Enter city: ").strip()
        if city:  # ✅ validation: must not be empty
            break
        else:
            print("City name cannot be empty. Please try again.")

    get_weather(api_key, city)
