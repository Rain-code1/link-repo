# Link – Route Finder and Optimizer

This project is a Python desktop application that helps users plan routes between two locations.

It uses:
- **GraphHopper** for routing
- **OpenStreetMap** for map tiles
- **Open-Meteo** for destination weather
- **PySide6** for the GUI
- **Leaflet** for the embedded map (inside `map_template.html`)

## Features

- Choose starting location and destination
- Select **Mode of Transport**: car, bike, or foot
- **Toll Roads** option: Use Toll Roads / Avoid Toll Roads
- **Fuel estimator** for car:
  - Car L/100 km
  - Fuel Price per liter
  - Shows estimated fuel usage and cost for the trip
- **Weather at Destination** with Celsius/Fahrenheit toggle
- Turn-by-turn instructions in a table
- Route shown on the map

## How to run the application

```bash
python main.py
