import pygame
import sys
import math
import random

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ракета 'Союз-М' — Посадка на Луну")

# Цвета
BLACK = (20, 20, 30)
BRICK_COLOR = (100, 60, 40)
ACCENT = (180, 120, 80)

# Ракетка «Союз-М»
RED_NOSE = (225, 40, 40)
RED_ACCENT = (195, 30, 30)
CYAN_GLASS = (130, 220, 250)

# Текст
TEXT_COLOR = (255, 215, 0)
TEXT_SHADOW = (30, 30, 40)

# Параметры ракетки
rocket_w = 46
rocket_h = 96
rocket_x = WIDTH // 2 - rocket_w // 2
rocket_y = HEIGHT - rocket_h - 10
rocket_speed = 4

# Кубики
cube_size = 40

# Платформы на Земле
platforms = []
for x in range(0, WIDTH, cube_size):
    platforms.append(pygame.Rect(x, HEIGHT - cube_size, cube_size, cube_size))
for y in range(0, HEIGHT - cube_size * 2, cube_size):
    platforms.append(pygame.Rect(0, y, cube_size, cube_size))
    platforms.append(pygame.Rect(WIDTH - cube_size, y, cube_size, cube_size))
platforms.append(pygame.Rect(160, 420, cube_size * 3, cube_size))
platforms.append(pygame.Rect(520, 320, cube_size * 2, cube_size))

# Увеличенный космонавт (высота 36px)
cosmo_h = 36
cosmo_w = 20
cosmo_x = 160
cosmo_y = HEIGHT - cube_size - cosmo_h
cosmo_speed = 2.0
cosmo_waving_timer = 0

# Состояние миссии
state = "EARTH_READY"
countdown_timer = 0
clock = pygame.time.Clock()
FPS = 60

# Звёзды в космосе
stars = [((i * 73 + 15) % WIDTH, (i * 37 + 23) % (HEIGHT - 120), (i % 2) + 1) for i in range(50)]

# Лунная поверхность и кратеры
lunar_ground_y = HEIGHT - 60
craters = [(120, HEIGHT - 35, 35, 12), (320, HEIGHT - 25, 20, 8), (650, HEIGHT - 40, 50, 15), (480, HEIGHT - 20, 15, 6)]

# Частицы пыли и дыма
particles = []


def draw_earth_in_space():
    ex, ey, er = 680, 100, 36
    pygame.draw.circle(screen, (30, 80, 180), (ex, ey), er)
    pygame.draw.circle(screen, (50, 140, 70), (ex - 8, ey - 6), 14)
    pygame.draw.circle(screen, (50, 140, 70), (ex + 10, ey + 12), 12)
    pygame.draw.circle(screen, (220, 240, 255), (ex + 6, ey - 10), 10)
    pygame.draw.circle(screen, (20, 20, 30), (ex + er - 6, ey), er, width=4)


def draw_moon_surface(frame_count):
    for sx, sy, sr in stars:
        brightness = 180 + int(60 * math.sin(frame_count * 0.05 + sx))
        pygame.draw.circle(screen, (brightness, brightness, brightness), (sx, sy), sr)

    draw_earth_in_space()

    # Рельеф Луны
    pygame.draw.rect(screen, (100, 100, 110), (0, lunar_ground_y, WIDTH, HEIGHT - lunar_ground_y))
    pygame.draw.line(screen, (150, 150, 165), (0, lunar_ground_y), (WIDTH, lunar_ground_y), 3)

    # Кратеры
    for cx, cy, rx, ry in craters:
        pygame.draw.ellipse(screen, (65, 65, 75), (cx - rx, cy - ry, rx * 2, ry * 2))
        pygame.draw.ellipse(screen, (130, 130, 145), (cx - rx, cy - ry, rx * 2, ry * 2), width=2)

    # Посадочная площадка
    pad_rect = pygame.Rect(WIDTH // 2 - 60, lunar_ground_y - 8, 120, 10)
    pygame.draw.rect(screen, (130, 130, 140), pad_rect)
    pygame.draw.rect(screen, (180, 180, 190), pad_rect, width=2)

    # Сигнальные огни
    light_color = (255, 60, 60) if (frame_count // 30) % 2 == 0 else (255, 220, 0)
    pygame.draw.circle(screen, light_color, (WIDTH // 2 - 50, lunar_ground_y - 4), 3)
    pygame.draw.circle(screen, light_color, (WIDTH // 2 + 50, lunar_ground_y - 4), 3)


def draw_flag(x, y):
    pygame.draw.line(screen, (220, 220, 230), (x, y), (x, y - 56), 3)
    flag_rect = (x, y - 56, 32, 20)
    pygame.draw.rect(screen, (210, 30, 30), flag_rect)
    pygame.draw.circle(screen, (255, 215, 0), (x + 9, y - 46), 4)


def draw_cosmonaut(x, y, frame_count, is_walking=False, waving=False, facing_right=True):
    # Рюкзак жизнеобеспечения (крупный)
    backpack_x = x - 6 if facing_right else x + 16
    pygame.draw.rect(screen, (180, 180, 195), (backpack_x, y + 10, 7, 18))
    pygame.draw.rect(screen, (70, 70, 80), (backpack_x, y + 10, 7, 18), width=1)

    # Скафандр (тело)
    pygame.draw.rect(screen, (245, 245, 250), (x, y + 10, 17, 16))
    pygame.draw.rect(screen, (60, 60, 70), (x, y + 10, 17, 16), width=1)

    # Красная полоса на скафандре и нашивка
    pygame.draw.rect(screen, (220, 40, 40), (x + 2, y + 14, 13, 3))
    pygame.draw.circle(screen, (70, 160, 240), (x + 5, y + 21), 2)  # панель приборов
    pygame.draw.circle(screen, (255, 200, 40), (x + 11, y + 21), 2)

    # Шлем (увеличенный круглый)
    helmet_cx = x + 8
    helmet_cy = y + 7
    pygame.draw.circle(screen, (245, 245, 250), (helmet_cx, helmet_cy), 8)
    pygame.draw.circle(screen, (60, 60, 70), (helmet_cx, helmet_cy), 8, width=1)

    # Забрало шлема (стекло)
    visor_x = x + 6 if facing_right else x + 2
    pygame.draw.rect(screen, CYAN_GLASS, (visor_x, y + 4, 8, 6))
    pygame.draw.rect(screen, (50, 80, 100), (visor_x, y + 4, 8, 6), width=1)
    # Блик на стекле
    pygame.draw.line(screen, (255, 255, 255), (visor_x + 1, y + 5), (visor_x + 3, y + 5), 1)

    # Руки
    if waving:
        # Анимация машущей руки
        arm_wave_offset = int(math.sin(frame_count * 0.3) * 4)
        pygame.draw.line(screen, (245, 245, 250), (x + 8, y + 12), (x + 18, y - 6 + arm_wave_offset), 4)
        pygame.draw.circle(screen, (220, 40, 40), (x + 18, y - 6 + arm_wave_offset), 3)  # красная перчатка
    else:
        arm_offset = int(math.sin(frame_count * 0.25) * 4) if is_walking else 0
        pygame.draw.line(screen, (245, 245, 250), (x + 8, y + 12), (x + 8 + arm_offset, y + 22), 4)
        pygame.draw.circle(screen, (220, 40, 40), (x + 8 + arm_offset, y + 23), 2)

    # Ножки с ботинками (анимация шагов)
    if is_walking:
        step = int(math.sin(frame_count * 0.3) * 5)
        # Левая нога
        pygame.draw.line(screen, (245, 245, 250), (x + 4, y + 26), (x + 4 - step, y + 34), 4)
        pygame.draw.rect(screen, (70, 70, 80), (x + 2 - step, y + 33, 5, 3))
        # Правая нога
        pygame.draw.line(screen, (245, 245, 250), (x + 13, y + 26), (x + 13 + step, y + 34), 4)
        pygame.draw.rect(screen, (70, 70, 80), (x + 11 + step, y + 33, 5, 3))
    else:
        pygame.draw.line(screen, (245, 245, 250), (x + 4, y + 26), (x + 4, y + 34), 4)
        pygame.draw.rect(screen, (70, 70, 80), (x + 2, y + 33, 5, 3))
        pygame.draw.line(screen, (245, 245, 250), (x + 13, y + 26), (x + 13, y + 34), 4)
        pygame.draw.rect(screen, (70, 70, 80), (x + 11, y + 33, 5, 3))


def draw_rocket(x, y, is_thrusting=False, deploy_legs=False, hatch_open=False):
    # 1. Посадочные опоры
    if deploy_legs:
        pygame.draw.line(screen, (160, 160, 170), (x - 6, y + rocket_h - 14), (x - 18, y + rocket_h + 8), 3)
        pygame.draw.line(screen, (120, 120, 130), (x - 24, y + rocket_h + 8), (x - 12, y + rocket_h + 8), 3)
        pygame.draw.line(screen, (160, 160, 170), (x + rocket_w + 6, y + rocket_h - 14), (x + rocket_w + 18, y + rocket_h + 8), 3)
        pygame.draw.line(screen, (120, 120, 130), (x + rocket_w + 12, y + rocket_h + 8), (x + rocket_w + 24, y + rocket_h + 8), 3)

    # 2. Боковые ускорители
    pygame.draw.rect(screen, (200, 200, 210), (x - 8, y + 36, 10, 48))
    pygame.draw.polygon(screen, RED_ACCENT, [(x - 8, y + 36), (x - 3, y + 28), (x + 2, y + 36)])
    pygame.draw.rect(screen, (200, 200, 210), (x + rocket_w - 2, y + 36, 10, 48))
    pygame.draw.polygon(screen, RED_ACCENT, [(x + rocket_w - 2, y + 36), (x + rocket_w + 3, y + 28), (x + rocket_w + 8, y + 36)])

    # 3. Белый корпус
    pygame.draw.rect(screen, (245, 245, 250), (x, y + 18, rocket_w, rocket_h - 26))
    pygame.draw.rect(screen, (70, 70, 80), (x, y + 18, rocket_w, rocket_h - 26), width=1)

    # 4. Красный колпачок
    nose = [(x + rocket_w // 2, y), (x, y + 18), (x + rocket_w, y + 18)]
    pygame.draw.polygon(screen, RED_NOSE, nose)
    pygame.draw.polygon(screen, (70, 70, 80), nose, width=1)

    # 5. Полосы
    pygame.draw.rect(screen, RED_ACCENT, (x, y + 26, rocket_w, 3))
    pygame.draw.rect(screen, RED_ACCENT, (x, y + rocket_h - 20, rocket_w, 3))

    # 6. Иллюминатор / Люк
    pygame.draw.circle(screen, (70, 70, 80), (x + rocket_w // 2, y + 36), 6)
    pygame.draw.circle(screen, CYAN_GLASS, (x + rocket_w // 2, y + 36), 4)

    # Входной люк (увеличен под нового космонавта)
    hatch_color = (60, 180, 80) if hatch_open else (90, 90, 100)
    pygame.draw.rect(screen, hatch_color, (x + 8, y + 54, 16, 22))
    pygame.draw.rect(screen, (50, 50, 60), (x + 8, y + 54, 16, 22), width=1)

    # 7. Надпись "СОЮЗ М"
    font_soiuz = pygame.font.SysFont("Arial", 8, bold=True)
    text_soiuz = font_soiuz.render("СОЮЗ М", True, (40, 40, 50))
    screen.blit(text_soiuz, (x + 25, y + 60))

    # 8. Сопла
    pygame.draw.rect(screen, (70, 70, 80), (x + 8, y + rocket_h - 8, rocket_w - 16, 8))

    # 9. Пламя
    if is_thrusting:
        flame_len = 35 if state == "FLYING_UP" else 18
        pygame.draw.polygon(screen, (255, 140, 0), [(x + 8, y + rocket_h), (x + rocket_w - 8, y + rocket_h), (x + rocket_w // 2, y + rocket_h + flame_len)])
        pygame.draw.polygon(screen, (255, 215, 0), [(x + 14, y + rocket_h), (x + rocket_w - 14, y + rocket_h), (x + rocket_w // 2, y + rocket_h + int(flame_len * 0.6))])


def draw_platforms():
    for platform in platforms:
        pygame.draw.rect(screen, BRICK_COLOR, platform)
        pygame.draw.rect(screen, ACCENT, platform, width=2)
        half = cube_size // 2
        pygame.draw.line(screen, ACCENT, (platform.x, platform.y + half), (platform.x + half, platform.y + half), 1)
        pygame.draw.line(screen, ACCENT, (platform.x + half, platform.y), (platform.x + half, platform.y + half), 1)


def draw_dendy_text(text, center_x, center_y, size=64, color=TEXT_COLOR):
    font = pygame.font.SysFont("Arial", size, bold=True)
    shadow_surf = font.render(text, True, TEXT_SHADOW)
    screen.blit(shadow_surf, shadow_surf.get_rect(center=(center_x + 2, center_y + 2)))
    text_surf = font.render(text, True, color)
    screen.blit(text_surf, text_surf.get_rect(center=(center_x, center_y)))


frame_count = 0
running = True
while running:
    clock.tick(FPS)
    frame_count += 1
    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and state == "EARTH_READY":
                state = "COSMO_WALKING"
            elif event.key == pygame.K_r and state == "LANDED":
                state = "EARTH_READY"
                rocket_y = HEIGHT - rocket_h - 10
                cosmo_x = 160
                cosmo_y = HEIGHT - cube_size - cosmo_h
                particles.clear()

    # === ЛОГИКА СОСТОЯНИЙ ===
    if state == "EARTH_READY":
        draw_platforms()
        draw_rocket(rocket_x, rocket_y, is_thrusting=False, deploy_legs=False, hatch_open=True)
        draw_cosmonaut(cosmo_x, cosmo_y, frame_count, is_walking=False, waving=False, facing_right=True)
        draw_dendy_text("НАЖМИТЕ ПРОБЕЛ — ПОСАДКА И ПУСК!", WIDTH // 2, 70, size=24, color=(200, 200, 220))

    elif state == "COSMO_WALKING":
        draw_platforms()
        hatch_target_x = rocket_x + 8

        if cosmo_x < hatch_target_x:
            cosmo_x += cosmo_speed
            draw_cosmonaut(cosmo_x, cosmo_y, frame_count, is_walking=True, waving=False, facing_right=True)
            draw_rocket(rocket_x, rocket_y, is_thrusting=False, deploy_legs=False, hatch_open=True)
        else:
            cosmo_waving_timer += 1
            draw_rocket(rocket_x, rocket_y, is_thrusting=False, deploy_legs=False, hatch_open=True)
            draw_cosmonaut(cosmo_x, cosmo_y, frame_count, is_walking=False, waving=True, facing_right=True)
            draw_dendy_text("ПОСАДКА В РАКЕТУ...", WIDTH // 2, 70, size=24, color=(255, 215, 0))

            if cosmo_waving_timer > 70:
                state = "COUNTDOWN"
                countdown_timer = 90
                cosmo_waving_timer = 0

    elif state == "COUNTDOWN":
        draw_platforms()
        countdown_timer -= 1
        draw_rocket(rocket_x, rocket_y, is_thrusting=False, deploy_legs=False, hatch_open=False)

        # Дым перед стартом
        if random.random() < 0.6:
            particles.append({
                'x': rocket_x + rocket_w // 2 + random.randint(-15, 15),
                'y': rocket_y + rocket_h - 2,
                'vx': random.uniform(-1.5, 1.5),
                'vy': random.uniform(0.5, 1.8),
                'r': random.randint(3, 8),
                'life': 30
            })

        for p in particles:
            if p['life'] > 0:
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['life'] -= 1
                pygame.draw.circle(screen, (150, 150, 160), (int(p['x']), int(p['y'])), p['r'])

        sec = (countdown_timer // 30) + 1
        if sec > 1:
            draw_dendy_text(f"ЗАПУСК ЧЕРЕЗ: {sec}", WIDTH // 2, 70, size=28, color=(255, 140, 0))
        else:
            draw_dendy_text("ПУСК! 🚀", WIDTH // 2, 70, size=36, color=(255, 60, 60))

        if countdown_timer <= 0:
            state = "FLYING_UP"
            particles.clear()

    elif state == "FLYING_UP":
        rocket_y -= rocket_speed
        draw_platforms()
        draw_rocket(rocket_x, rocket_y, is_thrusting=True, deploy_legs=False, hatch_open=False)

        if rocket_y <= -rocket_h - 30:
            state = "MOON_DESCENDING"
            rocket_y = -rocket_h

    elif state == "MOON_DESCENDING":
        draw_moon_surface(frame_count)
        target_land_y = lunar_ground_y - rocket_h - 6
        rocket_y += 2.0

        thrust_active = (frame_count // 6) % 2 == 0
        deploy_legs = (rocket_y > 150)
        draw_rocket(rocket_x, int(rocket_y), is_thrusting=thrust_active, deploy_legs=deploy_legs, hatch_open=False)

        if rocket_y >= target_land_y:
            rocket_y = target_land_y
            state = "COSMO_MOON_WALK"
            cosmo_x = rocket_x + 8
            cosmo_y = lunar_ground_y - cosmo_h
            for _ in range(30):
                particles.append({
                    'x': rocket_x + rocket_w // 2 + random.randint(-25, 25),
                    'y': lunar_ground_y - 2,
                    'vx': random.uniform(-2.5, 2.5),
                    'vy': random.uniform(-1.5, -0.2),
                    'r': random.randint(3, 7),
                    'life': random.randint(25, 50)
                })

    elif state == "COSMO_MOON_WALK":
        draw_moon_surface(frame_count)

        for p in particles:
            if p['life'] > 0:
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['life'] -= 1
                pygame.draw.circle(screen, (160, 160, 175), (int(p['x']), int(p['y'])), p['r'])

        draw_rocket(rocket_x, int(rocket_y), is_thrusting=False, deploy_legs=True, hatch_open=True)

        target_flag_x = rocket_x + rocket_w + 35
        if cosmo_x < target_flag_x:
            cosmo_x += 1.2
            draw_cosmonaut(cosmo_x, cosmo_y, frame_count, is_walking=True, waving=False, facing_right=True)
            draw_dendy_text("ВЫСАДКА НА ЛУНУ...", WIDTH // 2, 70, size=24, color=(100, 240, 130))
        else:
            draw_flag(target_flag_x, lunar_ground_y - 4)
            draw_cosmonaut(cosmo_x, cosmo_y, frame_count, is_walking=False, waving=True, facing_right=False)
            state = "LANDED"

    elif state == "LANDED":
        draw_moon_surface(frame_count)
        draw_rocket(rocket_x, int(rocket_y), is_thrusting=False, deploy_legs=True, hatch_open=True)
        draw_flag(rocket_x + rocket_w + 35, lunar_ground_y - 4)
        draw_cosmonaut(rocket_x + rocket_w + 35, lunar_ground_y - cosmo_h, frame_count, is_walking=False, waving=True, facing_right=False)

        draw_dendy_text("СОЮЗ-М", WIDTH // 2, HEIGHT // 2 - 70, size=64, color=(255, 215, 0))
        draw_dendy_text("ПОСАДКА НА ЛУНУ УСПЕШНА!", WIDTH // 2, HEIGHT // 2, size=32, color=(100, 240, 130))
        draw_dendy_text("НАЖМИТЕ [R] ДЛЯ ПОВТОРА", WIDTH // 2, HEIGHT // 2 + 55, size=22, color=(200, 200, 210))

    pygame.display.flip()

pygame.quit()
sys.exit()