import sys
import polyline
import json
import urllib.parse
import requests

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QComboBox, QPushButton,
    QVBoxLayout, QGridLayout, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QHBoxLayout, QSplitter
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from PySide6.QtWebEngineWidgets import QWebEngineView

# It's recommended to place this in a separate file for modularity
from route_downloads import download_route

# GraphHopper API Key from RouteOptimization.txt
API_KEY = "2e2cf02b-63b2-456a-a2d1-e1d04d28d6d1"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# --- Helper Functions (from RouteOptimization.txt) ---
def geocode(location_name: str):
    """Validate location using GraphHopper API and return coordinates or an error."""
    if not location_name.strip():
        return None, "Location name cannot be empty."

    params = {
        "q": location_name,
        "locale": "en",
        "limit": 1,
        "key": API_KEY
    }
    
    try:
        response = requests.get("https://graphhopper.com/api/1/geocode", params=params, timeout=30)
        response.raise_for_status() # Will raise an exception for HTTP error codes
    except requests.RequestException as e:
        return None, f"API error: {e}"

    data = response.json()
    hits = data.get("hits", [])
    if not hits:
        return None, f"Invalid location: '{location_name}'. Please try again."

    point = hits[0]["point"]
    return (point["lat"], point["lng"]), None

def call_route(start_lat, start_lng, end_lat, end_lng, vehicle, avoid_tolls=False):
    base = "https://graphhopper.com/api/1/route"
    params = [
        ("point", f"{start_lat},{start_lng}"),
        ("point", f"{end_lat},{end_lng}"),
        ("vehicle", vehicle),
        ("locale", "en"),
        ("points_encoded", "true"),
        ("key", API_KEY),
    ]

    if avoid_tolls:
        # This parameter enables the custom_model feature
        params.append(("ch.disable", "true"))


        custom_model = {
          "priority": [
            {
              "if": "toll == ALL",
              "multiply_by": 0.1
            }
          ]
        }
        
        params.append(("custom_model", json.dumps(custom_model)))

    try:
        r = requests.get(base, params=params, timeout=45)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        # This will now correctly catch and print the specific error from the API
        print(f"API call error: {e}")
        # It's helpful to also print the response text to see the exact error message
        if e.response is not None:
            print(f"API response: {e.response.text}")
        return {}

def estimate_fuel(distance_km: float, l_per_100: float):
    try:
        return (distance_km * float(l_per_100)) / 100.0
    except (ValueError, TypeError):
        return None

# --- Main Application Class ---
class RouteFinder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Link - Route Finder and Optimizer")
        self.setFixedSize(1200, 700)
        self.setStyleSheet("background-color: #ecddd4; color: black;")
        self.init_ui()
        self.on_vehicle_change() # Set initial state

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        left_panel = QVBoxLayout()
        grid = QGridLayout()
        grid.setSpacing(10)

        # --- Input Fields ---
        grid.addWidget(QLabel("Starting Location:"), 0, 0)
        self.entry_start = QLineEdit(placeholderText="e.g., Manila")
        grid.addWidget(self.entry_start, 0, 1)

        grid.addWidget(QLabel("Destination:"), 1, 0)
        self.entry_end = QLineEdit(placeholderText="e.g., Quezon City")
        grid.addWidget(self.entry_end, 1, 1)

        grid.addWidget(QLabel("Mode of Transport:"), 2, 0)
        self.combo_vehicle = QComboBox()
        self.combo_vehicle.addItems(["car", "bike", "foot"])
        self.combo_vehicle.currentTextChanged.connect(self.on_vehicle_change)
        grid.addWidget(self.combo_vehicle, 2, 1)

        self.label_tolls = QLabel("Toll Roads:") # <-- Assign the label to self.label_tolls
        grid.addWidget(self.label_tolls, 3, 0)   # <-- Use the new variable here
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Use Toll Roads", "Avoid Toll Roads"])
        grid.addWidget(self.combo_mode, 3, 1)

        self.label_fuel_economy = QLabel("Car L/100 km:")
        grid.addWidget(self.label_fuel_economy, 4, 0)
        self.entry_fuel_economy = QLineEdit("8.0")
        grid.addWidget(self.entry_fuel_economy, 4, 1)

        self.label_fuel_price = QLabel("Fuel Price (per L):")
        grid.addWidget(self.label_fuel_price, 5, 0)
        self.entry_fuel_price = QLineEdit("75.0")
        grid.addWidget(self.entry_fuel_price, 5, 1)

        grid.addWidget(QLabel("Temp Unit:"), 6, 0)
        self.combo_temp_unit = QComboBox()
        self.combo_temp_unit.addItems(["celsius", "fahrenheit"])
        grid.addWidget(self.combo_temp_unit, 6, 1)

        self.weather_label = QLabel("Weather: --")
        self.weather_label.setFont(QFont("Segoe UI", 10))

        
        left_panel.addWidget(self.weather_label)

        left_panel.addLayout(grid)


        # --- Buttons ---
        btn_layout = QHBoxLayout()
        self.btn_route = QPushButton("Get Route")
        self.btn_route.clicked.connect(self.get_route)
        self.btn_route.setStyleSheet("background-color: #2e7d32; color: white; font-weight: 600; padding: 6px 12px; border-radius: 4px;")
        btn_layout.addWidget(self.btn_route)

        self.btn_download = QPushButton("Download")
        self.btn_download.clicked.connect(self.download)
        self.btn_download.setStyleSheet("background-color: #f9a825; color: white; font-weight: 600; padding: 6px 12px; border-radius: 4px;")
        btn_layout.addWidget(self.btn_download)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self.clear_fields)
        self.btn_clear.setStyleSheet("background-color: #c62828; color: white; font-weight: 600; padding: 6px 12px; border-radius: 4px;")
        btn_layout.addWidget(self.btn_clear)
        left_panel.addLayout(btn_layout)

        # --- Results and Table ---
        self.result_label = QLabel("")
        self.result_label.setStyleSheet("color: black;")
        self.result_label.setFont(QFont("Segoe UI", 10))
        left_panel.addWidget(self.result_label)

        self.table = QTableWidget(columnCount=3)
        self.table.setHorizontalHeaderLabels(["Step", "Instruction", "Distance (km)"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False) # <-- ADD THIS LINE
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                color: black;
            }
            QHeaderView::section {
                background-color: #442d26;
                color: white;
                font-weight: 600;
                padding: 4px;
                border: none;
            }
        """)

        left_panel.addWidget(self.table)

        # ✅ Input fields style should be here (after they’re created above)
        self.entry_start.setStyleSheet("background-color: white; color: black;")
        self.entry_end.setStyleSheet("background-color: white; color: black;")
        self.entry_fuel_economy.setStyleSheet("background-color: white; color: black;")
        self.entry_fuel_price.setStyleSheet("background-color: white; color: black;")

        self.combo_vehicle.setStyleSheet("background-color: white; color: black;")
        self.combo_mode.setStyleSheet("background-color: white; color: black;")
        self.combo_temp_unit.setStyleSheet("background-color: white; color: black;")

        # --- Map View ---
        self.map_view = QWebEngineView()
        self.load_map()

        # --- Splitter Layout ---
        splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        splitter.addWidget(left_widget)
        splitter.addWidget(self.map_view)
        splitter.setSizes([500, 700])
        main_layout.addWidget(splitter)

    def on_vehicle_change(self):
        is_car = self.combo_vehicle.currentText() == "car"
        self.label_fuel_economy.setVisible(is_car)
        self.entry_fuel_economy.setVisible(is_car)
        self.label_fuel_price.setVisible(is_car)
        self.entry_fuel_price.setVisible(is_car)
        self.label_tolls.setVisible(is_car)
        self.combo_mode.setVisible(is_car)
        self.combo_mode.setEnabled(is_car) # Optimization only for car

    def get_route(self):
        start = self.entry_start.text().strip()
        end = self.entry_end.text().strip()
        vehicle = self.combo_vehicle.currentText()
        mode = self.combo_mode.currentText()
        
        start_coords, error_start = geocode(start)
        if error_start:
            QMessageBox.critical(self, "Input Error", f"Starting Location Error: {error_start}")
            return

        end_coords, error_end = geocode(end)
        if error_end:
            QMessageBox.critical(self, "Input Error", f"Destination Error: {error_end}")
            return

        start_lat, start_lng = start_coords
        end_lat, end_lng = end_coords

        try:
            # Check the user's choice for toll roads
            avoid_tolls = (mode == "Avoid Toll Roads")
            
            # Call the updated routing function
            data = call_route(start_lat, start_lng, end_lat, end_lng, vehicle, avoid_tolls=avoid_tolls)

            if "paths" in data and data["paths"]:
                path = data["paths"][0]
                distance = path["distance"] / 1000
                time = path["time"] / 60000

                fuel_text = ""
                if vehicle == "car":
                    fuel_l = estimate_fuel(distance, self.entry_fuel_economy.text())
                    if fuel_l is not None:
                        try:
                            price = float(self.entry_fuel_price.text())
                            cost = fuel_l * price
                            fuel_text = f"\nEstimated Fuel: {fuel_l:.2f} L | Est. Cost: ₱{cost:.2f}"
                        except ValueError:
                            fuel_text = "\nInvalid fuel price."

                # Update the result label to show the toll preference
                label = "Route (Avoiding Tolls)" if avoid_tolls else "Route (Using Tolls)"
                self.result_label.setText(f"<b>{label}</b>\nDistance: {distance:.2f} km\nEstimated Time: {time:.1f} minutes{fuel_text}")
                
                instructions = path["instructions"]
                self.table.setRowCount(len(instructions))
                for i, step in enumerate(instructions):
                    self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                    self.table.setItem(i, 1, QTableWidgetItem(step["text"]))
                    self.table.setItem(i, 2, QTableWidgetItem(f"{step['distance'] / 1000:.2f}"))

                coords = polyline.decode(path["points"])
                self.load_map(coords, (start_lat, start_lng), (end_lat, end_lng))
                self.get_weather(end_lat, end_lng)
            else:
                self.result_label.setText("Error: Could not find a route.")
        except Exception as e:
            self.result_label.setText(f"An error occurred: {e}")

    # Loads the map template and injects route data into it
    def load_map(self, route_coords=None, start=None, end=None):
        route_js = ""
        if route_coords:
            route_js += f"""
                var route = {json.dumps(route_coords)};
                var polyline = L.polyline(route, {{color: 'blue'}}).addTo(map);
                map.fitBounds(polyline.getBounds());
            """
        if start and end:
            route_js += f"""
                L.marker([{start[0]}, {start[1]}]).addTo(map).bindPopup("Start").openPopup();
                L.marker([{end[0]}, {end[1]}]).addTo(map).bindPopup("End");
            """

        try:
            with open("map_template.html", "r", encoding="utf-8") as file:
                html = file.read()
            html = html.replace("// ROUTE_JS will be injected here", route_js)
            self.map_view.setHtml(html)
        except Exception as e:
            QMessageBox.critical(self, "Map Load Error", f"Could not load map: {str(e)}")

    def get_weather(self, lat, lon):
        """Fetch weather for the destination using Open-Meteo API."""
        unit = self.combo_temp_unit.currentText()
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": "true",
            "temperature_unit": unit
        }
        
        try:
            response = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=15)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            data = response.json()
            temp = data["current_weather"]["temperature"]
            unit_symbol = "°C" if unit == "celsius" else "°F"
            
            self.weather_label.setText(f"Weather at Destination: {temp}{unit_symbol}")
            
        except requests.RequestException as e:
            self.weather_label.setText("Weather: Could not retrieve data.")
            print(f"Weather API error: {e}")

    def clear_fields(self):
        self.entry_start.clear()
        self.entry_end.clear()
        self.combo_vehicle.setCurrentText("car")
        self.combo_mode.setCurrentText("Fastest")
        self.entry_fuel_economy.setText("8.0")
        self.entry_fuel_price.setText("75.0")
        self.result_label.setText("")
        self.table.setRowCount(0)
        self.load_map()

    def download(self):
        # This function needs access to the UI elements
        if not self.entry_start.text() or not self.entry_end.text():
             QMessageBox.warning(self, "Download Error", "Please generate a route first.")
             return
        download_route(self.entry_start, self.entry_end, self.combo_vehicle, self.result_label, self.table, self.combo_mode, self.weather_label)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RouteFinder()
    window.show()
    sys.exit(app.exec())