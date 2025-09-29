import tkinter as tk
from tkinter import ttk, messagebox
import requests
import urllib.parse
import os

# GraphHopper API Key (replace with your own valid key)
API_KEY = "e12d52ab-3595-42e7-b9a3-7cc7866a2401"

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
            distance = data["paths"][0]["distance"] / 1000
            time = data["paths"][0]["time"] / 60000
            result_text.set(f"Distance: {distance:.2f} km\nEstimated Time: {time:.2f} minutes")

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
    result_text.set("")
    clear_table()

def download_route():
    route_info = result_text.get()
    if not route_info or "Error" in route_info:
        messagebox.showwarning("Download Error", "No valid route information to download.")
        return

    try:
        # Create 'saved_routes' directory if it doesn't exist
        folder_path = os.path.join(os.getcwd(), "saved_routes")
        os.makedirs(folder_path, exist_ok=True)

        # Extract first words
        start_word = entry_start.get().strip().split()[0]
        end_word = entry_end.get().strip().split()[0]
        vehicle = combo_vehicle.get().capitalize()

        # Base filename
        base_name = f"{start_word}{end_word}{vehicle}"
        file_name = base_name + ".txt"
        file_path = os.path.join(folder_path, file_name)

        # Check for duplicates and iterate
        counter = 1
        while os.path.exists(file_path):
            file_name = f"{base_name}({counter}).txt"
            file_path = os.path.join(folder_path, file_name)
            counter += 1

        # Write to file
        with open(file_path, "w", encoding="utf-8") as file:
            file.write("Route Information\n")
            file.write("=================\n")
            file.write(f"Start: {entry_start.get()}\n")
            file.write(f"End: {entry_end.get()}\n")
            file.write(f"Vehicle: {combo_vehicle.get()}\n\n")
            file.write(route_info + "\n\n")
            file.write("Step-by-Step Directions:\n")
            file.write("-------------------------\n")
            file.write("{:<6} {:<60} {:>10}\n".format("Step", "Instruction", "Distance (km)"))
            file.write("="*80 + "\n")
            for row in directions_table.get_children():
                step, instruction, distance = directions_table.item(row)["values"]
                file.write("{:<6} {:<60} {:>10}\n".format(step, instruction, distance))

        messagebox.showinfo("Download Complete", f"Route saved to:\n{file_path}")
    except Exception as e:
        messagebox.showerror("File Error", f"Could not save file: {str(e)}")

# Main window
root = tk.Tk()
root.title("Route Finder")
root.geometry("700x550")
root.resizable(False, False)

# Layout
frame = ttk.Frame(root, padding=10)
frame.pack(fill="both", expand=True)

# Start location
ttk.Label(frame, text="Starting Location:").grid(row=0, column=0, sticky="w")
entry_start = ttk.Entry(frame, width=40)
entry_start.grid(row=0, column=1, pady=5)

# End location
ttk.Label(frame, text="Destination:").grid(row=1, column=0, sticky="w")
entry_end = ttk.Entry(frame, width=40)
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
ttk.Button(btn_frame, text="Download", command=download_route).pack(side="left", padx=5)

# Result display
result_text = tk.StringVar()
result_label = ttk.Label(frame, textvariable=result_text, foreground="blue", justify="left")
result_label.grid(row=4, column=0, columnspan=2, pady=10)

# Table container
table_frame = ttk.Frame(frame)
table_frame.grid(row=5, column=0, columnspan=2, pady=5)

# Scrollbar
scrollbar = ttk.Scrollbar(table_frame, orient="vertical")
scrollbar.pack(side="right", fill="y")

# Directions table
directions_table = ttk.Treeview(table_frame, columns=("Step", "Instruction", "Distance"), show="headings", height=10, yscrollcommand=scrollbar.set)
directions_table.heading("Step", text="Step")
directions_table.heading("Instruction", text="Instruction")
directions_table.heading("Distance", text="Distance (km)")
directions_table.column("Step", width=60, anchor="center")
directions_table.column("Instruction", width=460, anchor="w")
directions_table.column("Distance", width=120, anchor="center")
directions_table.pack(side="left", fill="x", expand=True)

scrollbar.config(command=directions_table.yview)

# Run
root.mainloop()
