from PyQt6.QtWidgets import QApplication
from window import MainWindow
import sys


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
