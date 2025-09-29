import tkinter as tk
from tkinter import ttk, messagebox
import requests

GRAPHOPPER_API_KEY = "94cc9301-76da-4df6-9912-fbf7a84a86e6"
GRAPHOPPER_URL = "https://graphhopper.com/api/1/geocode"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

def validate_city(city_name):
    """Validate city using GraphHopper API"""
    if not city_name.strip():
        return None, "City name cannot be empty."
    params = {"q": city_name, "locale": "en", "limit": 1, "key": GRAPHOPPER_API_KEY}
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
    temp_unit = "fahrenheit" if unit == "imperial" else "celsius"
    params = {"latitude": lat, "longitude": lon, "current_weather": True, "temperature_unit": temp_unit}
    response = requests.get(OPEN_METEO_URL, params=params)
    if response.status_code != 200:
        return None, f"Weather API error: {response.status_code}"
    data = response.json()
    if "current_weather" not in data:
        return None, "No weather data available."
    temp = data["current_weather"]["temperature"]
    return temp, None

def get_weather_button():
    city_input = entry_city.get().strip()
    unit_choice = combo_unit.get()
    city_info, err = validate_city(city_input)
    if err:
        messagebox.showerror("Error", err)
        return
    city, country, lat, lon = city_info
    temp, err = get_weather(lat, lon, unit_choice)
    if err:
        messagebox.showerror("Error", err)
        return
    unit_label = "°C" if unit_choice == "metric" else "°F"
    result_text.set(f"✅ City found: {city}, {country}\n🌡 Temperature: {temp} {unit_label}")

def clear_fields():
    entry_city.delete(0, tk.END)
    combo_unit.set("metric")
    result_text.set("")

# GUI Setup
root = tk.Tk()
root.title("Weather Finder")
root.geometry("400x250")
root.resizable(False, False)

frame = ttk.Frame(root, padding=10)
frame.pack(fill="both", expand=True)

ttk.Label(frame, text="City:").grid(row=0, column=0, sticky="w")
entry_city = ttk.Entry(frame, width=30)
entry_city.grid(row=0, column=1, pady=5)

ttk.Label(frame, text="Units:").grid(row=1, column=0, sticky="w")
combo_unit = ttk.Combobox(frame, values=["metric", "imperial"], state="readonly")
combo_unit.set("metric")
combo_unit.grid(row=1, column=1, pady=5)

btn_frame = ttk.Frame(frame)
btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
ttk.Button(btn_frame, text="Get Weather", command=get_weather_button).pack(side="left", padx=5)
ttk.Button(btn_frame, text="Clear", command=clear_fields).pack(side="left", padx=5)

result_text = tk.StringVar()
ttk.Label(frame, textvariable=result_text, foreground="blue", justify="left").grid(row=3, column=0, columnspan=2, pady=10)

root.mainloop()