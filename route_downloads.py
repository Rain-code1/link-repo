import os
from PySide6.QtWidgets import QMessageBox

def download_route(
    entry_start,
    entry_end,
    combo_vehicle,
    result_text,
    directions_table,
    combo_mode,
    weather_label
):
    """
    Save the current route details to a text file in a 'saved_routes' folder.

    Parameters:
        entry_start      (QLineEdit): Starting location input.
        entry_end        (QLineEdit): Destination input.
        combo_vehicle    (QComboBox): Mode of transport (car/bike/foot).
        result_text      (QLabel): Summary label (distance, time, fuel, cost).
        directions_table (QTableWidget): Step-by-step instructions table.
        combo_mode       (QComboBox): Toll roads option (Use / Avoid).
        weather_label    (QLabel): Weather at destination label.
    """

    # Raw HTML/text from the summary label
    route_info_raw = result_text.text().strip()
    optimization = combo_mode.currentText().strip() if combo_mode else "N/A"
    weather_info = weather_label.text().strip() if weather_label else "N/A"

    # Basic validation
    if not route_info_raw or "Error" in route_info_raw:
        QMessageBox.warning(None, "Download Error", "No valid route information to download.")
        return

    # Clean some simple HTML tags so the file looks nicer
    route_info = (
        route_info_raw
        .replace("<b>", "")
        .replace("</b>", "")
        .replace("<br>", "\n")
        .replace("<br/>", "\n")
        .replace("<br />", "\n")
    )

    try:
        # Ensure saved_routes folder exists
        folder_path = os.path.join(os.getcwd(), "saved_routes")
        os.makedirs(folder_path, exist_ok=True)

        # Build base filename from first word of start + end + vehicle
        start_word = entry_start.text().strip().split()[0] if entry_start.text().strip() else "Start"
        end_word = entry_end.text().strip().split()[0] if entry_end.text().strip() else "End"
        vehicle = combo_vehicle.currentText().capitalize() if combo_vehicle else "Vehicle"

        base_name = f"{start_word}{end_word}{vehicle}"
        file_name = base_name + ".txt"
        file_path = os.path.join(folder_path, file_name)

        # Avoid overwriting existing files
        counter = 1
        while os.path.exists(file_path):
            file_name = f"{base_name}({counter}).txt"
            file_path = os.path.join(folder_path, file_name)
            counter += 1

        # If vehicle is not car, toll optimization doesn't really apply
        if combo_vehicle and combo_vehicle.currentText() != "car":
            optimization_display = "N/A (not applicable for this mode)"
        else:
            optimization_display = optimization

        with open(file_path, "w", encoding="utf-8") as file:
            # Header information
            file.write("Route Information\n")
            file.write("=================\n")
            file.write(f"Start          : {entry_start.text().strip()}\n")
            file.write(f"End            : {entry_end.text().strip()}\n")
            file.write(f"Vehicle        : {combo_vehicle.currentText() if combo_vehicle else 'N/A'}\n")
            file.write(f"Toll Mode      : {optimization_display}\n")
            file.write(f"Weather Status : {weather_info}\n\n")

            file.write("Route Summary\n")
            file.write("-------------\n")
            file.write(route_info + "\n\n")

            # Step-by-step directions table
            file.write("Step-by-Step Directions:\n")
            file.write("-------------------------\n")
            file.write("{:<6} {:<60} {:>10}\n".format("Step", "Instruction", "Distance (km)"))
            file.write("=" * 80 + "\n")

            row_count = directions_table.rowCount()
            for row in range(row_count):
                step_item = directions_table.item(row, 0)
                instr_item = directions_table.item(row, 1)
                dist_item = directions_table.item(row, 2)

                step = step_item.text() if step_item else str(row + 1)
                instruction = instr_item.text() if instr_item else ""
                distance = dist_item.text() if dist_item else ""

                file.write("{:<6} {:<60} {:>10}\n".format(step, instruction, distance))

        QMessageBox.information(None, "Download Complete", f"Route saved to:\n{file_path}")

    except Exception as e:
        QMessageBox.critical(None, "File Error", f"Could not save file: {str(e)}")
