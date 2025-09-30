import tkinter as tk
from tkinter import ttk, messagebox
import requests
import urllib.parse
from route_downloads import download_route  # Modular download logic

# GraphHopper API Key
API_KEY = "2ed9d9ad-9c16-42db-9afc-ae3c69373316"

def geocode(location):
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
        start_lat, start_lng = geocode(start)
        end_lat, end_lng = geocode(end)

        if not start_lat or not end_lat:
            result_text.set("Error: Could not geocode one of the locations.")
            clear_table()
            return

        url = f"https://graphhopper.com/api/1/route?point={start_lat},{start_lng}&point={end_lat},{end_lng}&vehicle={vehicle}&locale=en&key={API_KEY}"
        response = requests.get(url)
        data = response.json()

        if "paths" in data:
            distance = data["paths"][0]["distance"] / 1000  # in km
            time = data["paths"][0]["time"] / 60000  # in minutes
            
            # --- START: New code for fuel cost calculation ---
            results_str = f"Distance: {distance:.2f} km\nEstimated Time: {time:.2f} minutes"

            if vehicle == 'car':
                try:
                    fuel_economy = float(entry_fuel_economy.get())
                    fuel_price = float(entry_fuel_price.get())
                    if fuel_economy <= 0:
                        messagebox.showwarning("Input Error", "Fuel economy must be greater than zero.")
                        return

                    fuel_needed = distance / fuel_economy
                    estimated_cost = fuel_needed * fuel_price
                    results_str += f"\nEstimated Fuel Cost: ${estimated_cost:.2f}"

                except ValueError:
                    messagebox.showwarning("Input Error", "Please enter valid numbers for fuel economy and price.")
                    return
            
            result_text.set(results_str)
            # --- END: New code for fuel cost calculation ---

            clear_table()
            instructions = data["paths"][0]["instructions"]
            for i, step in enumerate(instructions, start=1):
                text = step["text"]
                dist_km = step["distance"] / 1000
                directions_table.insert("", "end", values=(i, text, f"{dist_km:.2f}"))
        else:
            result_text.set("Error: Could not find route.")
            clear_table()
    except Exception as e:
        result_text.set(f"Error: {str(e)}")
        clear_table()

def clear_table():
    for row in directions_table.get_children():
        directions_table.delete(row)

def clear_fields():
    entry_start.delete(0, tk.END)
    entry_end.delete(0, tk.END)
    combo_vehicle.set("car")
    # --- START: Clear new fuel fields ---
    entry_fuel_economy.delete(0, tk.END)
    entry_fuel_price.delete(0, tk.END)
    # --- END: Clear new fuel fields ---
    result_text.set("")
    clear_table()

# Main window
root = tk.Tk()
root.title("Route Finder")
root.geometry("700x650") # Increased height for new fields
root.resizable(False, False)

frame = ttk.Frame(root, padding=10)
frame.pack(fill="both", expand=True)

# Input fields
ttk.Label(frame, text="Starting Location:").grid(row=0, column=0, sticky="w")
entry_start = ttk.Entry(frame, width=40)
entry_start.grid(row=0, column=1, pady=5)

ttk.Label(frame, text="Destination:").grid(row=1, column=0, sticky="w")
entry_end = ttk.Entry(frame, width=40)
entry_end.grid(row=1, column=1, pady=5)

ttk.Label(frame, text="Vehicle:").grid(row=2, column=0, sticky="w")
combo_vehicle = ttk.Combobox(frame, values=["car", "bike", "foot"], state="readonly")
combo_vehicle.set("car")
combo_vehicle.grid(row=2, column=1, pady=5)

# --- START: New GUI fields for fuel cost ---
ttk.Label(frame, text="Fuel Economy (km/L):").grid(row=3, column=0, sticky="w")
entry_fuel_economy = ttk.Entry(frame, width=40)
entry_fuel_economy.grid(row=3, column=1, pady=5)

ttk.Label(frame, text="Fuel Price (per Liter):").grid(row=4, column=0, sticky="w")
entry_fuel_price = ttk.Entry(frame, width=40)
entry_fuel_price.grid(row=4, column=1, pady=5)
# --- END: New GUI fields for fuel cost ---

# Buttons
btn_frame = ttk.Frame(frame)
btn_frame.grid(row=5, column=0, columnspan=2, pady=10) # Adjusted row

ttk.Button(btn_frame, text="Get Route", command=get_route).pack(side="left", padx=5)
ttk.Button(btn_frame, text="Clear", command=clear_fields).pack(side="left", padx=5)
ttk.Button(btn_frame, text="Download", command=lambda: download_route(entry_start, entry_end, combo_vehicle, result_text, directions_table)).pack(side="left", padx=5)

# Result summary
result_text = tk.StringVar()
result_label = ttk.Label(frame, textvariable=result_text, foreground="blue", justify="left")
result_label.grid(row=6, column=0, columnspan=2, pady=10) # Adjusted row

# Table container
table_frame = ttk.Frame(frame)
table_frame.grid(row=7, column=0, columnspan=2, pady=5) # Adjusted row

scrollbar = ttk.Scrollbar(table_frame, orient="vertical")
scrollbar.pack(side="right", fill="y")

directions_table = ttk.Treeview(table_frame, columns=("Step", "Instruction", "Distance"), show="headings", height=10, yscrollcommand=scrollbar.set)
directions_table.heading("Step", text="Step")
directions_table.heading("Instruction", text="Instruction")
directions_table.heading("Distance", text="Distance (km)")
directions_table.column("Step", width=60, anchor="center")
directions_table.column("Instruction", width=460, anchor="w")
directions_table.column("Distance", width=120, anchor="center")
directions_table.pack(side="left", fill="x", expand=True)

scrollbar.config(command=directions_table.yview)

root.mainloop()