import sys
import pygame
import requests


def error(res):
    print("Ошибка выполнения запроса:")
    print("Http статус:", res.status_code, "(", res.reason, ")")
    sys.exit(1)


def load_data():
    try:
        coords = map(float, input('Введите координаты: ').split())
        scale = map(float, input('Введите мастштаб: ').split())
    except Exception:
        print('Вводите нормальные данные')
    else:
        return coords, scale


def load_image(coords, scale):
    static_api_server = 'https://static-maps.yandex.ru/1.x/'
    params_static = {
        'll': ','.join(map(str, coords)),
        'spn': ','.join(map(str, scale)),
        'l': 'map'
    }
    response = requests.get(static_api_server, params=params_static)

    if not response:
        error(response)

    with open('map.png', 'wb') as file:
        file.write(response.content)


def main():
    coords, scale = load_data()
    load_image(coords, scale)

    pygame.init()
    screen = pygame.display.set_mode((600, 450))
    screen.blit(pygame.image.load('map.png'), (0, 0))
    pygame.display.flip()
    while pygame.event.wait().type != pygame.QUIT:
        pass
    pygame.quit()


if __name__ == '__main__':
    main()
