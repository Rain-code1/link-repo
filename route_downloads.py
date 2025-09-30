import os
from PySide6.QtWidgets import QMessageBox

def download_route(entry_start, entry_end, combo_vehicle, result_text, directions_table, combo_mode, weather_label):
    route_info = result_text.text()
    optimization = combo_mode.currentText()   # <-- get selected mode
    weather_info = weather_label.text() if weather_label else "N/A"
    
    if not route_info or "Error" in route_info:
        QMessageBox.warning(None, "Download Error", "No valid route information to download.")
        return

    try:
        folder_path = os.path.join(os.getcwd(), "saved_routes")
        os.makedirs(folder_path, exist_ok=True)

        start_word = entry_start.text().strip().split()[0]
        end_word = entry_end.text().strip().split()[0]
        vehicle = combo_vehicle.currentText().capitalize()

        base_name = f"{start_word}{end_word}{vehicle}"
        file_name = base_name + ".txt"
        file_path = os.path.join(folder_path, file_name)

        counter = 1
        while os.path.exists(file_path):
            file_name = f"{base_name}({counter}).txt"
            file_path = os.path.join(folder_path, file_name)
            counter += 1

        with open(file_path, "w", encoding="utf-8") as file:
            file.write("Route Information\n")
            file.write("=================\n")
            file.write(f"Start: {entry_start.text()}\n")
            file.write(f"End: {entry_end.text()}\n")
            file.write(f"Vehicle: {combo_vehicle.currentText()}\n")
            file.write(f"Optimization: {optimization}\n")
            file.write(f"Weather at Destination: {weather_info}\n\n")
            file.write(route_info + "\n\n")
            file.write("Step-by-Step Directions:\n")
            file.write("-------------------------\n")
            file.write("{:<6} {:<60} {:>10}\n".format("Step", "Instruction", "Distance (km)"))
            file.write("="*80 + "\n")

            for row in range(directions_table.rowCount()):
                step = directions_table.item(row, 0).text()
                instruction = directions_table.item(row, 1).text()
                distance = directions_table.item(row, 2).text()
                file.write("{:<6} {:<60} {:>10}\n".format(step, instruction, distance))

        QMessageBox.information(None, "Download Complete", f"Route saved to:\n{file_path}")
    except Exception as e:
        QMessageBox.critical(None, "File Error", f"Could not save file: {str(e)}")
