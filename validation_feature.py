import tkinter as tk
from tkinter import ttk, messagebox
import requests

GRAPHOPPER_API_KEY = "94cc9301-76da-4df6-9912-fbf7a84a86e6"
GRAPHOPPER_URL = "https://graphhopper.com/api/1/geocode"

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

def check_city():
    city_input = entry_city.get().strip()
    city_info, err = validate_city(city_input)
    if err:
        messagebox.showerror("Error", err)
        return

    city, country, lat, lon = city_info
    result_text.set(f"✅ City found: {city}, {country}\nLatitude: {lat}, Longitude: {lon}")

def clear_fields():
    entry_city.delete(0, tk.END)
    result_text.set("")

# GUI Setup
root = tk.Tk()
root.title("City Validation")
root.geometry("400x200")
root.resizable(False, False)

frame = ttk.Frame(root, padding=10)
frame.pack(fill="both", expand=True)

ttk.Label(frame, text="City:").grid(row=0, column=0, sticky="w")
entry_city = ttk.Entry(frame, width=30)
entry_city.grid(row=0, column=1, pady=5)

ttk.Button(frame, text="Validate City", command=check_city).grid(row=1, column=0, columnspan=2, pady=5)
ttk.Button(frame, text="Clear", command=clear_fields).grid(row=2, column=0, columnspan=2)

result_text = tk.StringVar()
ttk.Label(frame, textvariable=result_text, foreground="blue", justify="left").grid(row=3, column=0, columnspan=2, pady=10)

root.mainloop()
