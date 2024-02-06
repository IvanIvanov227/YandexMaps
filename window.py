from PyQt6.QtGui import QPixmap, QShortcut, QKeySequence
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt
from PyQt6 import uic
import requests
import json

# Bober kurwa
# Чтобы запустить QtDesigner напишите в консоли "PyQt6-tools designer"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('GUI.ui', self)
        self.keys = self.set_apikey()
        self.map = QPixmap()
        # Метки
        self.mark = ''
        # Приписывание почтового индекса
        self.add_mail = False
        # Последний географический объект, который был найден
        self.toponym = None
        self.zoom = 17
        # Вид карты
        self.typ = 'map'
        # Центр карты
        self.cords = [60.583335, 56.964456]
        # Значения скорости перемещения карты в зависимости от зума
        self.values_speed = {2: 10, 3: 5, 4: 2, 5: 1, 6: 0.8, 7: 0.6, 8: 0.3, 9: 0.1, 10: 0.08,
                             11: 0.04, 12: 0.02, 13: 0.01, 14: 0.005, 15: 0.003, 16: 0.0015, 17: 0.0006,
                             18: 0.0003, 19: 0.0002, 20: 0.00015, 21: 0.0001}
        # Скорость перемещения карты
        self.move_speed = self.values_speed[self.zoom]
        self.map_view.addItems(['map', 'sat', 'skl'])
        self.map_view.currentTextChanged.connect(self.view_changed)
        self.connect_buttons()
        self.update_map()

    @staticmethod
    def set_apikey():
        """Считывает ключи API"""
        with open('keys.json') as file:
            return json.load(file)

    def view_changed(self, view):
        """Меняет вид карты"""
        self.typ = view
        self.update_map()

    @staticmethod
    def check_zoom(zoom: int):
        """Проверяет корректность значения zoom"""
        # если поставить меньше, то у карты масштаб поменяется
        if zoom > 21 or zoom < 2:
            return False
        return True

    @staticmethod
    def check_cords(cords: list[float | int, float | int]):
        """Проверяет корректность значения центра карты"""
        if cords[1] > 90 or cords[1] < -90 or cords[0] > 180 or cords[0] < -180:
            return False
        return True

    def connect_buttons(self):
        # тут кнопочки соединяем
        # Пайчарм на отсутствие коннекта ругается, но он лох слепой просто
        zoom_in = QShortcut(QKeySequence(Qt.Key.Key_PageUp), self)
        zoom_in.activated.connect(self.zoomout_map)

        zoom_out = QShortcut(QKeySequence(Qt.Key.Key_PageDown), self)
        zoom_out.activated.connect(self.zoomin_map)

        move_left = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        move_left.activated.connect(lambda: self.move([self.cords[0] - self.move_speed, self.cords[1]]))

        move_right = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        move_right.activated.connect(lambda: self.move([self.cords[0] + self.move_speed, self.cords[1]]))

        move_up = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        move_up.activated.connect(lambda: self.move([self.cords[0], self.cords[1] + self.move_speed]))

        move_down = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
        move_down.activated.connect(lambda: self.move([self.cords[0], self.cords[1] - self.move_speed]))

        self.find_toponym_button.clicked.connect(self.find_toponym)
        self.reset_search.clicked.connect(self.delete_search)

        self.add_mail_box.stateChanged.connect(self.changed_add_mail)

    def changed_add_mail(self, state):
        """Приписывать или нет почтовый индекс к адресу"""
        if state == 2:
            self.add_mail = True
        else:
            self.add_mail = False
        self.update_address_toponym()

    def not_find_object_message(self):
        """Выводит сообщения, что не нашёлся объект"""
        self.toponym = None
        self.error_message.setText('Не удалось найти объект!')
        self.address_toponym.clear()

    def delete_search(self):
        """Сброс поискового результата"""
        self.mark = ''
        self.toponym = None
        self.error_message.clear()
        self.address_toponym.clear()
        self.update_map()

    def find_toponym(self):
        """Находит топоним по запросу"""
        geocode_api_server = 'https://geocode-maps.yandex.ru/1.x/'
        geocode_params = {
            'apikey': self.keys['geocode'],
            'geocode': self.name_toponym.text(),
            'lang': 'ru_RU',
            'format': 'json'
        }

        response = requests.get(geocode_api_server, params=geocode_params)
        if not response:
            self.not_find_object_message()
        else:
            self.error_message.clear()
            json_response = response.json()
            try:
                toponym = json_response["response"]["GeoObjectCollection"][
                    "featureMember"][0]["GeoObject"]
            except IndexError:
                self.not_find_object_message()
                return
            self.toponym = toponym
            toponym_cord = toponym["Point"]["pos"].split()
            self.update_address_toponym()
            # Добавление метки в географическом месте, заданной в запросе
            pt = "{0},{1},{2}{3}{4}".format(toponym_cord[0], toponym_cord[1], 'pm2', 'gn', 'l')
            self.mark = pt
            self.cords = list(map(float, toponym_cord))
            self.update_map()

    def update_address_toponym(self):
        """Обновление адреса топонима после нового запроса"""
        if self.toponym is None:
            return
        toponym_address_formatted = self.toponym['metaDataProperty']['GeocoderMetaData']['Address']['formatted']
        if self.add_mail:
            toponym_address = self.toponym['metaDataProperty']['GeocoderMetaData']['Address']
            if 'postal_code' in toponym_address:
                mail_code = toponym_address['postal_code']
                toponym_address_formatted += '\nПочтовый индекс: {0}'.format(mail_code)
        self.address_toponym.setPlainText(toponym_address_formatted)

    def update_map(self):
        """Обновление карты"""
        image = self.load_map(self.cords, self.zoom, self.typ, self.mark)
        if image is not None:
            self.map.loadFromData(image)
        # не смотрим, что PyCharm ругается, ибо пайчарм - тот ещё дурачок, мы эту кнопку в uic.loadui в __init__ делали
        self.map_label.setPixmap(self.map)

    def zoomin_map(self):
        """Уменьшение zoom"""
        if self.check_zoom(self.zoom - 1):
            self.zoom -= 1
            self.move_speed = self.values_speed[self.zoom]
        self.update_map()

    def zoomout_map(self):
        """Увеличение zoom"""
        if self.check_zoom(self.zoom + 1):
            self.zoom += 1
            self.move_speed = self.values_speed[self.zoom]
        self.update_map()

    def move(self, cords):
        """Перемещение центра карты"""
        if self.check_cords(cords):
            self.cords = cords
            self.update_map()

    @staticmethod
    def load_map(cords: list[float | int, float | int], zoom: int, typ: str, pt: str):
        """Загрузка изображения карты"""
        server_url = 'https://static-maps.yandex.ru/1.x/'
        parameters = {'ll': ','.join(map(str, cords)),
                      'z': zoom,
                      'l': typ}
        if pt != '':
            parameters['pt'] = pt
        response = requests.get(server_url, params=parameters)
        if not response:
            print('Чёт пошло не так')
            print(f'ответ от сервера: {response}, код ответа: {response.status_code}')
            return None
        return response.content
