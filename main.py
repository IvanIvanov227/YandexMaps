import sys
import pygame
import requests


# kurwa

def error(res):
    print("Ошибка выполнения запроса:")
    print("Http статус:", res.status_code, "(", res.reason, ")")
    sys.exit(1)


def load_data():
    try:
        # coords = list(map(float, input('Введите координаты: ').split()))
        # scale = list(map(float, input('Введите мастштаб: ').split()))
        cords = 60, 57
        scale = 1, 1
    except ValueError:
        print('Вводите нормальные данные')
    else:
        return cords, scale


def load_image(coords, scale):
    static_api_server = 'https://static-maps.yandex.ru/1.x/'
    params_static = {
        'll': ','.join(map(str, coords)),
        'spn': ','.join(map(str, scale)),
        'l': 'map'
    }
    response = requests.get(static_api_server, params=params_static)
    print('REQUEST')

    if not response:
        error(response)
    with open('map.png', 'wb') as file:
        file.write(response.content)


def check_scale(scale):
    scale_1, scale_2 = scale
    new_scale = scale
    if scale_1 <= 0:
        new_scale[0] = 0.05
    if scale_2 <= 0:
        new_scale[1] = 0.05
    if scale_1 >= 90:
        new_scale[0] = 89
    if scale_2 >= 90:
        new_scale[1] = 89
    return new_scale


def main():
    coords, scale = load_data()
    load_image(coords, scale)
    

    pygame.init()
    screen = pygame.display.set_mode((600, 450))
    running = True
    map_im = pygame.image.load('map.png')

    scale_step = 0.4
    jump_scare = 0.05

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_PAGEUP]:
                    scale = check_scale([scale[0] + scale_step, scale[1] + scale_step])

                elif keys[pygame.K_PAGEDOWN]:
                    scale = check_scale([scale[0] - scale_step, scale[1] - scale_step])

                elif keys[pygame.K_UP]:
                    coords = [coords[0], coords[1] + jump_scare]
                elif keys[pygame.K_DOWN]:
                    coords = [coords[0], coords[1] - jump_scare]
                elif keys[pygame.K_LEFT]:
                    coords = [coords[0] - jump_scare, coords[1]]
                elif keys[pygame.K_RIGHT]:
                    coords = [coords[0] + jump_scare, coords[1]]

                load_image(coords, scale)
                map_im = pygame.image.load('map.png')




        screen.blit(map_im, (0, 0))
        pygame.display.flip()
    pygame.quit()


if __name__ == '__main__':
    main()
