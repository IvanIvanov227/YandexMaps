from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtGui import QPixmap, QShortcut, QKeySequence
from PyQt6.QtCore import Qt
from PyQt6 import uic
import requests
import sys

# Bober kurwa
# Чтобы запустить QtDesigner напишите в коносли "PyQt6-tools designer"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('GUI.ui', self)
        self.map = QPixmap()
        self.zoom = 12
        self.connect_buttons()
        self.update_map()

    def check_zoom(self):
        if self.zoom > 21:
            self.zoom = 21
        elif self.zoom < 2:
            self.zoom = 2  # если поставить меньше, то у карты масштаб поменяется

    def connect_buttons(self):
        # тут кнопочки соеденяем
        # Пайчарм на отсуствие коннекта ругается, но он лох слепой просто
        zoom_in = QShortcut(QKeySequence(Qt.Key.Key_PageUp), self)
        zoom_in.activated.connect(self.zoomin_map)

        zoom_out = QShortcut(QKeySequence(Qt.Key.Key_PageDown), self)
        zoom_out.activated.connect(self.zoomout_map)

    def update_map(self):
        self.map.loadFromData(self.load_map([60, 57], self.zoom, 'map'))
        # не смотрим, что PyCharm ругается, ибо пайчарм - тот ещё дурачок, мы эту кнопку в uic.loadui в __init__ делали
        self.map_label.setPixmap(self.map)

    def zoomin_map(self):
        self.zoom += 1
        self.check_zoom()
        self.update_map()

    def zoomout_map(self):
        self.zoom -= 1
        self.check_zoom()
        self.update_map()

    @staticmethod
    def load_map(cords: list[float | int, float | int], zoom: int, typ: str):
        server_url = 'https://static-maps.yandex.ru/1.x/'
        parameters = {'ll': ','.join(map(str, cords)),
                      'z': zoom,
                      'l': typ,
                      'apikey': '5e802ae4-1674-4833-bdac-044ca0b297af'}
        response = requests.get(server_url, params=parameters)
        if not response:
            print('Чёт пошло не так')
            print(f'ответ от сервера: {response}')
            sys.exit(404)
        return response.content


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
