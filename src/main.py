import FreeSimpleGUI as sg
import sys
import os
import logging
import traceback

IS_BUILT = getattr(sys, 'frozen', False) or "__compiled__" in dir()

if not IS_BUILT:
    logging.basicConfig(
        filename="debug.log",
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(message)s"
    )
else:
    logging.disable(logging.CRITICAL)
    

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def main():
    sg.theme("LightBlue3")

    layout = [
        [sg.Text("Select a template-based Excel file:")],
        [sg.Input(key="-FILE-"), sg.FileBrowse(file_types=(("Excel files", "*.xlsx;*.xls"),))],
        [sg.Button("Run", size=(10, 1)), sg.Button("Quit", size=(10, 1))],
        [sg.Output(size=(90, 20), key="-OUTPUT-")],
    ]

    if sys.platform == "darwin":
        window = sg.Window(
            "Thermal Index Calculator",
            layout
        )
    else:
        window = sg.Window(
            "Thermal Index Calculator",
            layout,
            icon=resource_path("TICalc.ico")
        )

    while True:
        event, values = window.read()
        if event in (sg.WINDOW_CLOSED, "Quit"):
            break

        if event == "Run":
            from ExcelRunner import run_excel_calculation
            file_path = values["-FILE-"]
            if not file_path:
                print("No file selected.")
                continue
            print(f"Starting calculation for: {file_path}")
            try:
                run_excel_calculation(file_path, sheet_name="Data")
                print("Results written to columns W and beyond.")
            except Exception as e:
                logging.exception("[Error]")
                print(f"[ERROR] {e}")

    window.close()

if __name__ == "__main__":
    main()