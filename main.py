import tkinter as tk
from tkinter import ttk, messagebox
import requests
import urllib.parse
from route_downloads import download_route  # Modular download logic

# GraphHopper API Key
API_KEY = "2ed9d9ad-9c16-42db-9afc-ae3c69373316" # It's recommended to use the key from the new file: "2e2cf02b-63b2-456a-a2d1-e1d04d28d6d1"

# --- Helper Functions ---
def geocode(location: str): 
    url = f"https://graphhopper.com/api/1/geocode?q={urllib.parse.quote(location)}&limit=1&key={API_KEY}" 
    r = requests.get(url, timeout=30) 
    r.raise_for_status() 
    data = r.json() 
    if data.get("hits"): 
        p = data["hits"][0]["point"] 
        return p["lat"], p["lng"] 
    return None, None 

def call_route(start_lat, start_lng, end_lat, end_lng, vehicle, shortest=False): 
    base = "https://graphhopper.com/api/1/route" 
    params = [ 
        ("point", f"{start_lat},{start_lng}"), 
        ("point", f"{end_lat},{end_lng}"), 
        ("vehicle", vehicle), 
        ("locale", "en"), 
        ("points_encoded", "false"), 
        ("key", API_KEY), 
    ]
    if shortest: 
        params.append(("ch.disable", "true")) 
        params.append(("weighting", "shortest")) 

    r = requests.get(base, params=params, timeout=45) 

    if shortest and r.status_code != 200: 
        params = [ 
            ("point", f"{start_lat},{start_lng}"), 
            ("point", f"{end_lat},{end_lng}"), 
            ("vehicle", vehicle), 
            ("locale", "en"), 
            ("points_encoded", "false"), 
            ("key", API_KEY), 
        ]
        r = requests.get(base, params=params, timeout=45) 

    r.raise_for_status() 
    return r.json() 

def estimate_fuel(distance_km: float, l_per_100: float): 
    try:
        return (distance_km * float(l_per_100)) / 100.0 
    except Exception:
        return None 

# --- UI Actions ---
def on_vehicle_change(_=None): 
    is_car = combo_vehicle.get() == "car" 
    state = "normal" if is_car else "disabled"
    fuel_label.configure(state=state) 
    entry_fuel_economy.configure(state=state) 
    # Add new price fields to the state change
    price_label.configure(state=state)
    entry_fuel_price.configure(state=state)


def get_route():
    start = entry_start.get().strip() 
    end = entry_end.get().strip() 
    vehicle = combo_vehicle.get() 
    mode = mode_var.get() 
    l100 = entry_fuel_economy.get().strip() 
    price_str = entry_fuel_price.get().strip()

    if not start or not end: 
        messagebox.showwarning("Input Error", "Please enter both start and destination.") 
        return

    try:
        start_lat, start_lng = geocode(start) 
        end_lat, end_lng = geocode(end) 

        if start_lat is None or end_lat is None: 
            result_text.set("Error: Could not geocode one of the locations.") 
            clear_table()
            return

        shortest = (mode == "shortest") 
        data = call_route(start_lat, start_lng, end_lat, end_lng, vehicle, shortest=shortest) 
        
        if not data.get("paths", []): 
            result_text.set("Error: Could not find route.") 
            clear_table()
            return

        path = data["paths"][0] 
        distance_km = (path.get("distance", 0) or 0) / 1000.0 
        time_min = (path.get("time", 0) or 0) / 60000.0 

        # Fuel and cost estimate for cars only
        fuel_txt = "" 
        if vehicle == "car": 
            try:
                fuel_l = estimate_fuel(distance_km, float(l100)) 
                fuel_price = float(price_str)
                if fuel_l is not None: 
                    cost = fuel_l * fuel_price
                    fuel_txt = f"\nEstimated Fuel: {fuel_l:.2f} L | Est. Cost: ₱{cost:.2f}" 
            except (ValueError, TypeError):
                messagebox.showwarning("Input Error", "Please enter valid numbers for L/100 km and Fuel Price.")
                return


        label = "Fastest (time)" if not shortest else "Fuel-Efficient (shortest distance)" 
        result_text.set( 
            f"{label}\nDistance: {distance_km:.2f} km\nTime: {time_min:.1f} min{fuel_txt}" 
        )

        clear_table()
        instructions = path["instructions"]
        for i, step in enumerate(instructions, start=1):
            text = step["text"]
            dist_km = step["distance"] / 1000
            directions_table.insert("", "end", values=(i, text, f"{dist_km:.2f}"))

    except requests.HTTPError as e: 
        result_text.set(f"HTTP error: {e}") 
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
    mode_var.set("fastest") 
    entry_fuel_economy.delete(0, tk.END) 
    entry_fuel_economy.insert(0, "8.0") 
    entry_fuel_price.delete(0, tk.END)
    entry_fuel_price.insert(0, "75.0") # Set default price
    result_text.set("") 
    clear_table()
    on_vehicle_change() 

# === Main window ===
root = tk.Tk()
root.title("Route Finder and Optimizer")
root.geometry("700x680") # Adjusted height
root.resizable(False, False)

frame = ttk.Frame(root, padding=10)
frame.pack(fill="both", expand=True)

# Input fields
ttk.Label(frame, text="Starting Location:").grid(row=0, column=0, sticky="w")
entry_start = ttk.Entry(frame, width=40)
entry_start.grid(row=0, column=1, pady=5, sticky="w")

ttk.Label(frame, text="Destination:").grid(row=1, column=0, sticky="w")
entry_end = ttk.Entry(frame, width=40)
entry_end.grid(row=1, column=1, pady=5, sticky="w")

ttk.Label(frame, text="Vehicle:").grid(row=2, column=0, sticky="w") 
combo_vehicle = ttk.Combobox(frame, values=["car", "bike", "foot"], state="readonly") 
combo_vehicle.set("car") 
combo_vehicle.grid(row=2, column=1, pady=5, sticky="w")
combo_vehicle.bind("<<ComboboxSelected>>", on_vehicle_change) 

ttk.Label(frame, text="Optimization:").grid(row=3, column=0, sticky="w") 
mode_var = tk.StringVar(value="fastest") 
mode_box = ttk.Combobox( 
    frame, textvariable=mode_var,
    values=["fastest", "shortest"],
    state="readonly"
)
mode_box.grid(row=3, column=1, pady=4, sticky="w") 

fuel_label = ttk.Label(frame, text="Car L/100 km:") 
fuel_label.grid(row=4, column=0, sticky="w") 
entry_fuel_economy = ttk.Entry(frame, width=15) 
entry_fuel_economy.grid(row=4, column=1, pady=5, sticky="w") 
entry_fuel_economy.insert(0, "8.0") 

# New Fuel Price field
price_label = ttk.Label(frame, text="Fuel Price (per L):")
price_label.grid(row=5, column=0, sticky="w")
entry_fuel_price = ttk.Entry(frame, width=15)
entry_fuel_price.grid(row=5, column=1, pady=5, sticky="w")
entry_fuel_price.insert(0, "75.0") # A default value for Manila

# Buttons
btn_frame = ttk.Frame(frame)
btn_frame.grid(row=6, column=0, columnspan=2, pady=10) # Adjusted row
ttk.Button(btn_frame, text="Get Route", command=get_route).pack(side="left", padx=5) 
ttk.Button(btn_frame, text="Clear", command=clear_fields).pack(side="left", padx=5) 
ttk.Button(btn_frame, text="Download", command=lambda: download_route(entry_start, entry_end, combo_vehicle, result_text, directions_table)).pack(side="left", padx=5)

# Result summary
result_text = tk.StringVar()
result_label = ttk.Label(frame, textvariable=result_text, foreground="blue", justify="left")
result_label.grid(row=7, column=0, columnspan=2, pady=10, sticky="w") # Adjusted row

# Table for directions
table_frame = ttk.Frame(frame)
table_frame.grid(row=8, column=0, columnspan=2, pady=5) # Adjusted row
scrollbar = ttk.Scrollbar(table_frame, orient="vertical")
scrollbar.pack(side="right", fill="y")
directions_table = ttk.Treeview(table_frame, columns=("Step", "Instruction", "Distance"), show="headings", height=8, yscrollcommand=scrollbar.set)
directions_table.heading("Step", text="Step")
directions_table.heading("Instruction", text="Instruction")
directions_table.heading("Distance", text="Distance (km)")
directions_table.column("Step", width=60, anchor="center")
directions_table.column("Instruction", width=460, anchor="w")
directions_table.column("Distance", width=120, anchor="center")
directions_table.pack(side="left", fill="x", expand=True)
scrollbar.config(command=directions_table.yview)

# Initialize UI state
on_vehicle_change() 

root.mainloop()