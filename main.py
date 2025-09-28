import tkinter as tk
from tkinter import ttk, messagebox
import requests
import urllib.parse


# GraphHopper API Key (replace with your own valid key)
API_KEY = "2e2cf02b-63b2-456a-a2d1-e1d04d28d6d1"


def geocode(location):
    """Get latitude and longitude for a location using GraphHopper Geocoding API"""
    url = f"https://graphhopper.com/api/1/geocode?q={urllib.parse.quote(location)}&limit=1&key={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if "hits" in data and len(data["hits"]) > 0:
        lat = data["hits"][0]["point"]["lat"]
        lng = data["hits"][0]["point"]["lng"]
        return lat, lng
    else:
        return None, None


def get_route():
    start = entry_start.get()
    end = entry_end.get()
    vehicle = combo_vehicle.get()


    if not start or not end:
        messagebox.showwarning("Input Error", "Please enter both start and destination.")
        return


    try:
        # Get coordinates for start and end
        start_lat, start_lng = geocode(start)
        end_lat, end_lng = geocode(end)


        if not start_lat or not end_lat:
            result_text.set("Error: Could not geocode one of the locations.")
            return


        # API URL for routing
        url = f"https://graphhopper.com/api/1/route?point={start_lat},{start_lng}&point={end_lat},{end_lng}&vehicle={vehicle}&locale=en&key={API_KEY}"


        # Send request
        response = requests.get(url)
        data = response.json()


        if "paths" in data:
            distance = data["paths"][0]["distance"] / 1000  # km
            time = data["paths"][0]["time"] / 60000  # minutes


            result_text.set(f"Distance: {distance:.2f} km\nEstimated Time: {time:.2f} minutes")
        else:
            result_text.set("Error: Could not find route.")
    except Exception as e:
        result_text.set(f"Error: {str(e)}")


def clear_fields():
    entry_start.delete(0, tk.END)
    entry_end.delete(0, tk.END)
    combo_vehicle.set("car")
    result_text.set("")


# Main window
root = tk.Tk()
root.title("Route Finder")
root.geometry("400x300")
root.resizable(False, False)


# Layout
frame = ttk.Frame(root, padding=10)
frame.pack(fill="both", expand=True)


# Start location
ttk.Label(frame, text="Starting Location:").grid(row=0, column=0, sticky="w")
entry_start = ttk.Entry(frame, width=30)
entry_start.grid(row=0, column=1, pady=5)


# End location
ttk.Label(frame, text="Destination:").grid(row=1, column=0, sticky="w")
entry_end = ttk.Entry(frame, width=30)
entry_end.grid(row=1, column=1, pady=5)


# Vehicle type
ttk.Label(frame, text="Vehicle:").grid(row=2, column=0, sticky="w")
combo_vehicle = ttk.Combobox(frame, values=["car", "bike", "foot"], state="readonly")
combo_vehicle.set("car")
combo_vehicle.grid(row=2, column=1, pady=5)


# Buttons
btn_frame = ttk.Frame(frame)
btn_frame.grid(row=3, column=0, columnspan=2, pady=10)


ttk.Button(btn_frame, text="Get Route", command=get_route).pack(side="left", padx=5)
ttk.Button(btn_frame, text="Clear", command=clear_fields).pack(side="left", padx=5)


# Result display
result_text = tk.StringVar()
result_label = ttk.Label(frame, textvariable=result_text, foreground="blue", justify="left")
result_label.grid(row=4, column=0, columnspan=2, pady=10)


# Run
root.mainloop()
