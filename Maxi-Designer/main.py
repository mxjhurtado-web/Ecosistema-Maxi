from view import MainWindow
from PyQt6.QtWidgets import QApplication
import sys
import traceback
import datetime

def log_crash(e):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("crash_log.txt", "a", encoding="utf-8") as f:
        f.write(f"\n[{timestamp}] FATAL CRASH: {e}\n")
        f.write(traceback.format_exc())
        f.write("-" * 40 + "\n")

def main():
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        log_crash(e)
        raise e

if __name__ == "__main__":
    main()
