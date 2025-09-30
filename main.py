import tkinter as tk
from tkinter import ttk, messagebox
import requests
import urllib.parse

# === CONFIG ===
API_KEY = "2e2cf02b-63b2-456a-a2d1-e1d04d28d6d1"  # replace with your own valid key

# --- helpers ---
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
    # ask for shortest when user selects fuel-efficient
    if shortest:
        params.append(("ch.disable", "true"))
        params.append(("weighting", "shortest"))

    r = requests.get(base, params=params, timeout=45)

    # if shortest isn’t supported by your plan/server, fallback silently to default
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

# --- actions ---
def on_vehicle_change(_=None):
    is_car = vehicle_var.get() == "car"
    fuel_label.configure(state=("normal" if is_car else "disabled"))
    fuel_entry.configure(state=("normal" if is_car else "disabled"))

def get_route():
    start = start_entry.get().strip()
    end = end_entry.get().strip()
    vehicle = vehicle_var.get()
    mode = mode_var.get()  # "fastest" or "shortest"
    l100 = fuel_entry.get().strip()

    if not start or not end:
        messagebox.showwarning("Input error", "Please enter both Start and Destination.")
        return

    try:
        s_lat, s_lng = geocode(start)
        e_lat, e_lng = geocode(end)
        if s_lat is None or e_lat is None:
            result_var.set("Could not geocode one of the locations.")
            return

        shortest = (mode == "shortest")
        data = call_route(s_lat, s_lng, e_lat, e_lng, vehicle, shortest=shortest)
        paths = data.get("paths", [])
        if not paths:
            result_var.set("No route found.")
            return

        p = paths[0]
        dist_km = (p.get("distance", 0) or 0) / 1000.0
        time_min = (p.get("time", 0) or 0) / 60000.0

        # fuel estimate for cars only
        fuel_txt = ""
        if vehicle == "car" and l100:
            fuel_l = estimate_fuel(dist_km, float(l100))
            if fuel_l is not None:
                fuel_txt = f"\nEstimated Fuel: {fuel_l:.2f} L"

        label = "Fastest (time)" if not shortest else "Fuel-Efficient (shortest distance)"
        result_var.set(
            f"{label}\nDistance: {dist_km:.2f} km\nTime: {time_min:.1f} min{fuel_txt}"
        )

    except requests.HTTPError as e:
        result_var.set(f"HTTP error: {e}")
    except Exception as e:
        result_var.set(f"Error: {e}")

def clear_all():
    start_entry.delete(0, tk.END)
    end_entry.delete(0, tk.END)
    vehicle_var.set("car")
    mode_var.set("fastest")
    fuel_entry.delete(0, tk.END)
    fuel_entry.insert(0, "8.0")
    result_var.set("")
    on_vehicle_change()

# === UI ===
root = tk.Tk()
root.title("Simple Route Optimizer")
root.geometry("420x340")
root.resizable(False, False)

pad = 10
frm = ttk.Frame(root, padding=pad)
frm.pack(fill="both", expand=True)

# Start
ttk.Label(frm, text="Start:").grid(row=0, column=0, sticky="w")
start_entry = ttk.Entry(frm, width=36)
start_entry.grid(row=0, column=1, pady=4, sticky="w")

# Destination
ttk.Label(frm, text="Destination:").grid(row=1, column=0, sticky="w")
end_entry = ttk.Entry(frm, width=36)
end_entry.grid(row=1, column=1, pady=4, sticky="w")

# Vehicle
ttk.Label(frm, text="Vehicle:").grid(row=2, column=0, sticky="w")
vehicle_var = tk.StringVar(value="car")
vehicle_box = ttk.Combobox(frm, textvariable=vehicle_var, values=["car", "bike", "foot"], state="readonly", width=12)
vehicle_box.grid(row=2, column=1, pady=4, sticky="w")
vehicle_box.bind("<<ComboboxSelected>>", on_vehicle_change)

# Mode (Fastest vs Fuel-Efficient)
ttk.Label(frm, text="Optimization:").grid(row=3, column=0, sticky="w")
mode_var = tk.StringVar(value="fastest")
mode_box = ttk.Combobox(
    frm, textvariable=mode_var,
    values=["fastest", "shortest"],  # fastest = time, shortest = distance
    state="readonly", width=12
)
mode_box.grid(row=3, column=1, pady=4, sticky="w")

# Fuel L/100km (only for car)
fuel_label = ttk.Label(frm, text="Car L/100 km:")
fuel_label.grid(row=4, column=0, sticky="w")
fuel_entry = ttk.Entry(frm, width=10)
fuel_entry.grid(row=4, column=1, pady=4, sticky="w")
fuel_entry.insert(0, "8.0")

# Buttons
btns = ttk.Frame(frm)
btns.grid(row=5, column=0, columnspan=2, pady=8)
ttk.Button(btns, text="Get Route", command=get_route).pack(side="left", padx=5)
ttk.Button(btns, text="Clear", command=clear_all).pack(side="left", padx=5)

# Result
result_var = tk.StringVar()
result_lbl = ttk.Label(frm, textvariable=result_var, foreground="blue", justify="left", wraplength=380)
result_lbl.grid(row=6, column=0, columnspan=2, pady=8, sticky="w")

# init
on_vehicle_change()

root.mainloop()