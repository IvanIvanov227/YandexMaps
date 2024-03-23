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
        self.size_image = 600, 450
        self.map = QPixmap()
        # Метки
        self.mark = ''
        # Приписывание почтового индекса
        self.add_mail = False
        # Последний географический объект, который был найден
        self.toponym = None
        self.bbox = [[60.579364, 56.962154], [60.587575, 56.966639]]
        # Вид карты
        self.typ = 'map'
        # Центр карты
        self.cords = [60.583335, 56.964456]
        # Значения скорости перемещения карты в зависимости от зума
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
    def check_zoom(spn: list):
        """Проверяет корректность значения zoom"""
        # если поставить меньше, то у карты масштаб поменяется
        if spn[0][0] > 180 or spn[1][0] < -180 or spn[0][1] > 90 or spn[1][1] < -90:
            return False
        elif spn[0][0] >= spn[1][0] or spn[0][1] >= spn[1][1]:
            return False
        return True

    @staticmethod
    def check_cords(cords: list[float | int, float | int]):
        """Проверяет корректность значения центра карты"""
        if cords[1] > 90 or cords[1] < -90 or cords[0] > 180 or cords[0] < -180:
            return False
        return True

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            x, y = event.pos().x(), event.pos().y()
            if x <= self.size_image[0] and y <= self.size_image[1]:
                cord_x = x / self.size_image[0]
                cord_y = (self.size_image[1] - y) / self.size_image[1]
                # Координаты нажатия
                point_x = self.bbox[0][0] + (cord_x * abs(self.bbox[0][0] - self.bbox[1][0]))
                point_y = self.bbox[0][1] + (cord_y * abs(self.bbox[0][1] - self.bbox[1][1]))
                self.find_toponym(f'{point_x}, {point_y}', update_cord=False)

    def connect_buttons(self):
        # тут кнопочки соединяем
        # Пайчарм на отсутствие коннекта ругается, но он лох слепой просто
        zoom_in = QShortcut(QKeySequence(Qt.Key.Key_PageUp), self)
        zoom_in.activated.connect(self.zoomout_map)

        zoom_out = QShortcut(QKeySequence(Qt.Key.Key_PageDown), self)
        zoom_out.activated.connect(self.zoomin_map)

        move_speed = abs(self.bbox[1][0] - self.bbox[0][0])
        move_left = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        move_left.activated.connect(lambda: self.move([-move_speed, 0]))

        move_right = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        move_right.activated.connect(lambda: self.move([move_speed, 0]))

        move_up = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        move_up.activated.connect(lambda: self.move([0, move_speed]))

        move_down = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
        move_down.activated.connect(lambda: self.move([0, -move_speed]))

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

    def find_toponym(self, find_text=None, update_cord=True):
        """Находит топоним по запросу"""
        geocode_api_server = 'https://geocode-maps.yandex.ru/1.x/'
        geocode_params = {
            'apikey': self.keys['geocode'],
            'geocode': self.name_toponym.text(),
            'lang': 'ru_RU',
            'format': 'json'
        }
        if find_text is not None:
            geocode_params['geocode'] = find_text

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
            if update_cord:
                envelope_lower = list(map(float, toponym['boundedBy']['Envelope']['lowerCorner'].split()))
                envelope_upper = list(map(float, toponym['boundedBy']['Envelope']['upperCorner'].split()))
                self.bbox = [envelope_lower, envelope_upper]
                self.cords = list(map(float, toponym_cord))

            self.update_address_toponym()
            # Добавление метки в географическом месте, заданной в запросе
            pt = "{0},{1},{2}{3}{4}".format(toponym_cord[0], toponym_cord[1], 'pm2', 'gn', 'l')
            self.mark = pt
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
        bbox = f'{self.bbox[0][0]},{self.bbox[0][1]}~{self.bbox[1][0]},{self.bbox[1][1]}'
        image = self.load_map(self.cords, bbox, self.typ, self.mark, self.size_image)
        if image is not None:
            self.map.loadFromData(image)
        self.map_label.setPixmap(self.map)

    def zoomin_map(self):
        """Уменьшение zoom"""
        delta = abs(self.bbox[1][0] - self.bbox[0][0]) / 10
        new_bbox = [[self.bbox[0][0] + delta, self.bbox[0][1] + delta], [self.bbox[1][0] - delta, self.bbox[1][1] - delta]]

        if self.check_zoom(new_bbox):
            self.bbox = new_bbox
        self.update_map()

    def zoomout_map(self):
        """Увеличение zoom"""
        delta = abs(self.bbox[1][0] - self.bbox[0][0]) / 10
        new_bbox = [[self.bbox[0][0] - delta, self.bbox[0][1] - delta], [self.bbox[1][0] + delta, self.bbox[1][1] + delta]]

        if self.check_zoom(new_bbox):
            self.bbox = new_bbox
        self.update_map()

    def move(self, cords):
        """Перемещение центра карты"""
        if self.check_cords([self.cords[0] + cords[0], self.cords[1] + cords[1]]):
            self.cords = [self.cords[0] + cords[0], self.cords[1] + cords[1]]
            self.bbox[0][1] += cords[1]
            self.bbox[1][1] += cords[1]
            self.bbox[0][0] += cords[0]
            self.bbox[1][0] += cords[0]
            self.update_map()

    @staticmethod
    def load_map(cords: list[float | int, float | int], spn: str, typ: str, pt: str, size: tuple):
        """Загрузка изображения карты"""
        server_url = 'https://static-maps.yandex.ru/1.x/'
        parameters = {'ll': ','.join(map(str, cords)),
                      'size': ','.join(map(str, size)),
                      'bbox': spn,
                      'l': typ}
        if pt != '':
            parameters['pt'] = pt
        response = requests.get(server_url, params=parameters)

        if not response:
            print('Чёт пошло не так')
            print(f'ответ от сервера: {response}, код ответа: {response.status_code}')
            return None
        return response.content
