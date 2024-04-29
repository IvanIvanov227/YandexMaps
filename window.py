from PyQt6.QtGui import QPixmap, QShortcut, QKeySequence
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt
from PyQt6 import uic
import requests
import json
import copy

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
        # Область показа
        self.bbox = None
        # Вид карты
        self.typ = 'map'
        self.run()

    def run(self):
        self.map_view.addItems(['map', 'sat', 'skl'])
        self.map_view.currentTextChanged.connect(self.view_changed)
        self.connect_buttons()
        self.name_toponym.setText('Верхняя Пышма, Успенский проспект, 2Г')
        self.find_toponym()
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
    def check_zoom(bbox: list):
        """Проверяет корректность значения zoom"""
        if bbox[0][0] > 180 or bbox[0][0] < -170 or bbox[1][0] > 180 or bbox[1][0] < -170:
            return False
        elif bbox[0][1] > 85 or bbox[0][1] < -85 or bbox[1][1] > 85 or bbox[1][1] < -85:
            return False
        elif bbox[0][0] >= bbox[1][0] or bbox[0][1] >= bbox[1][1]:
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
                cord_long, cord_width = get_cords(x, y, self.size_image, self.bbox)
                self.find_toponym(f'{cord_long},{cord_width}', update_bbox=False)

        elif event.button() == Qt.MouseButton.RightButton:
            x, y = event.pos().x(), event.pos().y()
            if x <= self.size_image[0] and y <= self.size_image[1]:
                cord_long, cord_width = get_cords(x, y, self.size_image, self.bbox)
                organization = get_organization((cord_long, cord_width))
                if organization is None:
                    self.organization_label.setText('Не найдена')
                else:
                    self.organization_label.setText(organization)

    def connect_buttons(self):
        # тут кнопочки соединяем
        # Пайчарм на отсутствие коннекта ругается, но он лох слепой просто
        zoom_in = QShortcut(QKeySequence(Qt.Key.Key_PageUp), self)
        zoom_in.activated.connect(self.zoomout_map)

        zoom_out = QShortcut(QKeySequence(Qt.Key.Key_PageDown), self)
        zoom_out.activated.connect(self.zoomin_map)

        move_left = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        move_left.activated.connect(lambda: self.move([-1, 0]))

        move_right = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        move_right.activated.connect(lambda: self.move([1, 0]))

        move_up = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        move_up.activated.connect(lambda: self.move([0, 1]))

        move_down = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
        move_down.activated.connect(lambda: self.move([0, -1]))

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

    def find_toponym(self, click_cord=None, update_bbox=True):
        """Находит топоним по запросу"""
        geocode_api_server = 'https://geocode-maps.yandex.ru/1.x/'
        geocode_params = {
            'apikey': self.keys['geocode'],
            'geocode': self.name_toponym.text(),
            'lang': 'ru_RU',
            'format': 'json'
        }
        if click_cord not in (False, None):
            geocode_params['geocode'] = click_cord

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
            print(toponym_cord)
            if update_bbox:
                envelope_lower = list(map(float, toponym['boundedBy']['Envelope']['lowerCorner'].split()))
                envelope_upper = list(map(float, toponym['boundedBy']['Envelope']['upperCorner'].split()))
                self.bbox = [envelope_lower, envelope_upper]

            if click_cord not in (None, False):
                # Добавление метки в географическом месте, где нажали мышкой
                pt = "{0},{1},{2}{3}{4}".format(click_cord.split(',')[0], click_cord.split(',')[1], 'pm2', 'gn', 'l')
            else:
                # Добавление метки в географическом месте, заданной в запросе
                pt = "{0},{1},{2}{3}{4}".format(toponym_cord[0], toponym_cord[1], 'pm2', 'gn', 'l')

            self.update_address_toponym()
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
        image = self.load_map(bbox, self.typ, self.mark, self.size_image)
        if image is not None:
            self.map.loadFromData(image)
        self.map_label.setPixmap(self.map)

    def zoomout_map(self):
        """Уменьшение zoom"""
        delta = abs(self.bbox[1][0] - self.bbox[0][0]) / 3
        new_bbox = [[self.bbox[0][0] + delta, self.bbox[0][1] + delta], [self.bbox[1][0] - delta, self.bbox[1][1] - delta]]

        if self.check_zoom(new_bbox):
            self.bbox = new_bbox
            self.update_map()

    def zoomin_map(self):
        """Увеличение zoom"""
        delta = abs(self.bbox[1][0] - self.bbox[0][0]) / 3
        new_bbox = [[self.bbox[0][0] - delta, self.bbox[0][1] - delta], [self.bbox[1][0] + delta, self.bbox[1][1] + delta]]

        if self.check_zoom(new_bbox):
            self.bbox = new_bbox
            self.update_map()

    def move(self, action):
        """Перемещение центра карты"""
        move_speed = abs(self.bbox[1][0] - self.bbox[0][0]) / 10
        new_bbox = copy.deepcopy(self.bbox)
        if action[0] == 0:
            new_bbox[0][1] += action[1] * move_speed
            new_bbox[1][1] += action[1] * move_speed
        else:
            new_bbox[0][0] += action[0] * move_speed
            new_bbox[1][0] += action[0] * move_speed

        if self.check_zoom(new_bbox):
            self.bbox = new_bbox
            self.update_map()

    @staticmethod
    def load_map(spn: str, typ: str, pt: str, size: tuple):
        """Загрузка изображения карты"""
        server_url = 'https://static-maps.yandex.ru/1.x/'
        parameters = {'size': ','.join(map(str, size)),
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


def get_organization(pos):
    x, y = pos
    search_api_server = 'https://search-maps.yandex.ru/v1/'
    params = {
        'apikey': '18efb559-e464-4f3f-84e9-99dcee4359bf',
        'text': str(x) + ', ' + str(y),
        'lang': 'ru_RU',
        'type': 'biz'
    }
    response = requests.get(search_api_server, params=params)
    print(response.url)
    json_response = response.json()
    if json_response['features']:
        name_org = json_response['features'][0]['properties']['CompanyMetaData']['name']
        return name_org
    else:
        return None


def get_cords(x, y, size_image, bbox):
    part_x = x / size_image[0]
    part_y = (size_image[1] - y) / size_image[1]
    # Координаты нажатия
    cord_long = bbox[0][0] + (part_x * abs(bbox[1][0] - bbox[0][0]))
    cord_width = bbox[0][1] + (part_y * abs(bbox[1][1] - bbox[0][1]))
    return cord_long, cord_width
