import polyline
import json
import urllib.parse
import requests
import os

# PySide6 GUI components
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QComboBox, QPushButton,
    QVBoxLayout, QGridLayout, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QHBoxLayout, QSplitter
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from PySide6.QtWebEngineWidgets import QWebEngineView

# External Module for saving route details
from route_downloads import download_route  # Your modular download logic

# GraphHopper API Key
API_KEY = "2ed9d9ad-9c16-42db-9afc-ae3c69373316"

# Geocode function: get latitude and longitude from a location name
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

# Main application class
class RouteFinder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Link - Route Finder")
        self.setFixedSize(1200, 600)
        self.setStyleSheet("background-color: #ecddd4;")
        self.init_ui()

     # Initializes all UI components and layout
    def init_ui(self):
        font = QFont("Segoe UI", 10)
        main_layout = QHBoxLayout(self)

        # Left panel
        left_panel = QVBoxLayout()

        # Input grid for start, end, and vehicle type
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(QLabel("Starting Location:"), 0, 0)
        self.entry_start = QLineEdit()
        self.entry_start.setPlaceholderText("e.g., Manila")
        self.entry_start.setStyleSheet("background-color: white;")
        grid.addWidget(self.entry_start, 0, 1)

        grid.addWidget(QLabel("Destination:"), 1, 0)
        self.entry_end = QLineEdit()
        self.entry_end.setPlaceholderText("e.g., Quezon City")
        self.entry_end.setStyleSheet("background-color: white;")
        grid.addWidget(self.entry_end, 1, 1)

        grid.addWidget(QLabel("Vehicle:"), 2, 0)
        self.combo_vehicle = QComboBox()
        self.combo_vehicle.addItems(["car", "bike", "foot"])
        self.combo_vehicle.setStyleSheet("background-color: white;")
        grid.addWidget(self.combo_vehicle, 2, 1)

        left_panel.addLayout(grid)

        # Button layout: Get Route, Download, Clear
        btn_layout = QHBoxLayout()
        
        self.btn_route = QPushButton("Get Route")
        self.btn_route.clicked.connect(self.get_route)
        btn_layout.addWidget(self.btn_route)

        self.btn_download = QPushButton("Download")
        self.btn_download.clicked.connect(self.download)
        btn_layout.addWidget(self.btn_download)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self.clear_fields)
        btn_layout.addWidget(self.btn_clear)

        # Custom styles for buttons
        self.btn_route.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;  /* Green */
                color: white;
                padding: 6px 12px;
                font-size: 10pt;
                font-weight: 600;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
        """)

        self.btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #c62828;  /* Red */
                color: white;
                padding: 6px 12px;
                font-size: 10pt;
                font-weight: 600;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)

        self.btn_download.setStyleSheet("""
            QPushButton {
                background-color: #f9a825;  /* Yellow */
                color: white;
                font-weight: 600;
                padding: 6px 12px;
                font-size: 10pt;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #fbc02d;
            }
        """)


        left_panel.addLayout(btn_layout)

        # Label to display route summary (distance and time)
        self.result_label = QLabel("")
        self.result_label.setFont(font)
        self.result_label.setStyleSheet("color: black;")
        left_panel.addWidget(self.result_label)

        # Table to display step-by-step instructions
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Step", "Instruction", "Distance (km)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Step
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)           # Instruction
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Distance

        self.table.setColumnWidth(0, 60)   # Step
        self.table.setColumnWidth(1, 300)  # Instruction
        self.table.setColumnWidth(2, 100)  # Distance

        self.table.setStyleSheet("""
            QHeaderView::section {
                background-color: #442d26;
                color: white;
                font-weight: 600;
                padding: 4px;
                border: none;
            }
            QTableWidget {
                background-color: white;
                color: black;
                font-size: 10pt;
            }
            QTableWidget::item {
                background-color: white;
                color: black;
            }
        """)
        left_panel.addWidget(self.table)

        # Right panel: map view
        self.map_view = QWebEngineView()
        self.load_map()

        # Splitter to separate left and right panels
        splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        splitter.addWidget(left_widget)
        splitter.addWidget(self.map_view)
        splitter.setSizes([500, 700])

        main_layout.addWidget(splitter)

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

    # Fetches route data from GraphHopper and updates UI
    def get_route(self):
        start = self.entry_start.text()
        end = self.entry_end.text()
        vehicle = self.combo_vehicle.currentText()

        if not start or not end:
            QMessageBox.warning(self, "Input Error", "Please enter both start and destination.")
            return

        try:
            start_lat, start_lng = geocode(start)
            end_lat, end_lng = geocode(end)

            if not start_lat or not end_lat:
                self.result_label.setText("Error: Could not geocode one of the locations.")
                self.table.setRowCount(0)
                return

            url = f"https://graphhopper.com/api/1/route?point={start_lat},{start_lng}&point={end_lat},{end_lng}&vehicle={vehicle}&locale=en&key={API_KEY}"
            response = requests.get(url)
            data = response.json()

            if "paths" in data:
                distance = data["paths"][0]["distance"] / 1000
                time = data["paths"][0]["time"] / 60000
                self.result_label.setText(f"Distance: {distance:.2f} km\nEstimated Time: {time:.2f} minutes")

                self.table.setRowCount(0)
                instructions = data["paths"][0]["instructions"]
                for i, step in enumerate(instructions):
                    self.table.insertRow(i)
                    self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                    self.table.setItem(i, 1, QTableWidgetItem(step["text"]))
                    self.table.setItem(i, 2, QTableWidgetItem(f"{step['distance'] / 1000:.2f}"))

                encoded = data["paths"][0]["points"]
                coords = polyline.decode(encoded)
                route_coords = [[lat, lng] for lat, lng in coords]
                self.load_map(route_coords, (start_lat, start_lng), (end_lat, end_lng))
            else:
                self.result_label.setText("Error: Could not find route.")
                self.table.setRowCount(0)
        except Exception as e:
            self.result_label.setText(f"Error: {str(e)}")
            self.table.setRowCount(0)

    def clear_fields(self):
        self.entry_start.clear()
        self.entry_end.clear()
        self.combo_vehicle.setCurrentText("car")
        self.result_label.setText("")
        self.table.setRowCount(0)
        self.load_map()

    def download(self):
        download_route(self.entry_start, self.entry_end, self.combo_vehicle, self.result_label, self.table)

if __name__ == "__main__":
    app = QApplication([])
    window = RouteFinder()
    window.show()
    app.exec()
