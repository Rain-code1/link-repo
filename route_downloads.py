import os
from tkinter import messagebox

def download_route(entry_start, entry_end, combo_vehicle, result_text, directions_table):
    route_info = result_text.get()
    if not route_info or "Error" in route_info:
        messagebox.showwarning("Download Error", "No valid route information to download.")
        return

    try:
        folder_path = os.path.join(os.getcwd(), "saved_routes")
        os.makedirs(folder_path, exist_ok=True)

        start_word = entry_start.get().strip().split()[0]
        end_word = entry_end.get().strip().split()[0]
        vehicle = combo_vehicle.get().capitalize()

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