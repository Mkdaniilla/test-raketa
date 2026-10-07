import asyncio
import pygame
import sys
import math
import random
import array

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ракета 'Союз-М' — Космическая Одиссея")

# Инициализация звука
HAS_SOUND = False
try:
    pygame.mixer.init(22050, -16, 1, 512)
    HAS_SOUND = True
except Exception:
    HAS_SOUND = False


def generate_sound(freq, duration_sec=0.1, wave_type="square", volume=0.25):
    if not HAS_SOUND:
        return None
    sample_rate = 22050
    n_samples = int(sample_rate * duration_sec)
    buf = array.array('h')
    for i in range(n_samples):
        t = i / sample_rate
        if wave_type == "square":
            val = 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0
        elif wave_type == "noise":
            val = random.uniform(-1.0, 1.0)
        else:
            val = math.sin(2 * math.pi * freq * t)
        decay = 1.0 - (i / n_samples)
        buf.append(int(val * 32767 * volume * decay))
    try:
        return pygame.mixer.Sound(buffer=buf)
    except Exception:
        return None


# Звуковые эффекты
snd_step = generate_sound(520, 0.04, "square", 0.15)
snd_beep = generate_sound(880, 0.08, "sine", 0.2)
snd_launch = generate_sound(220, 0.4, "square", 0.3)
snd_coin = generate_sound(1200, 0.12, "sine", 0.25)
snd_pop = generate_sound(600, 0.15, "noise", 0.2)


def play_sfx(snd):
    if HAS_SOUND and snd:
        try:
            snd.play()
        except Exception:
            pass


# Цвета
SKY_TOP = (15, 20, 35)
SKY_BOTTOM = (30, 45, 70)
CONCRETE_DARK = (40, 45, 55)
CONCRETE_LIGHT = (70, 75, 85)
TOWER_STEEL = (160, 50, 50)
TOWER_GRAY = (140, 145, 155)
YELLOW_HAZARD = (240, 190, 30)
BLACK_HAZARD = (25, 25, 30)

WHITE = (245, 245, 250)
RED_NOSE = (225, 40, 40)
RED_ACCENT = (195, 30, 30)
CYAN_GLASS = (130, 220, 250)
GOLD = (255, 215, 0)
TEXT_COLOR = (255, 215, 0)
TEXT_SHADOW = (30, 30, 40)

# Параметры ракетки
rocket_w = 46
rocket_h = 96
pad_ground_y = HEIGHT - 70
rocket_x = WIDTH // 2 - rocket_w // 2
rocket_y = pad_ground_y - rocket_h + 10
rocket_vx = 0.0
rocket_vy = 0.0

# Космонавт (36px)
cosmo_h = 36
cosmo_w = 20
cosmo_x = 130
cosmo_y = pad_ground_y - cosmo_h
cosmo_speed = 2.0
cosmo_waving_timer = 0

# Луноход-1
rover_x = 0
rover_y = 0
rover_w = 54
rover_h = 32
rover_vx = 0.0
rover_in_use = False

# Состояние миссии
# "EARTH_READY" -> "COSMO_WALKING" -> "COUNTDOWN" -> "SPACE_ARCADE" -> "LUNAR_LANDING" -> "ROVER_DEPLOY" -> "LUNAR_ROAMING"
state = "EARTH_READY"
countdown_timer = 0
mission_distance = 0.0
score = 0
fuel = 100.0
clock = pygame.time.Clock()
FPS = 60

# Звёзды и космические объекты
earth_stars = [((i * 89 + 23) % WIDTH, (i * 47 + 11) % 260, (i % 2) + 1) for i in range(40)]
space_stars = [{'x': random.randint(0, WIDTH), 'y': random.randint(0, HEIGHT), 'speed': random.uniform(1.0, 4.0), 'r': random.randint(1, 2)} for _ in range(70)]

# Астероиды и кристаллы
asteroids = []
crystals = []

# Лунная поверхность и кратеры
lunar_ground_y = HEIGHT - 60
craters = [(120, HEIGHT - 35, 35, 12), (320, HEIGHT - 25, 20, 8), (650, HEIGHT - 40, 50, 15), (480, HEIGHT - 20, 15, 6)]

# Частицы
particles = []
steam_particles = []
fireworks = []


def draw_earth_sky(frame_count):
    for y in range(0, pad_ground_y):
        ratio = y / pad_ground_y
        r = int(SKY_TOP[0] * (1 - ratio) + SKY_BOTTOM[0] * ratio)
        g = int(SKY_TOP[1] * (1 - ratio) + SKY_BOTTOM[1] * ratio)
        b = int(SKY_TOP[2] * (1 - ratio) + SKY_BOTTOM[2] * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    for sx, sy, sr in earth_stars:
        brightness = 170 + int(70 * math.sin(frame_count * 0.04 + sx))
        pygame.draw.circle(screen, (brightness, brightness, brightness), (sx, sy), sr)

    for x in range(0, WIDTH, 24):
        h = 25 + int(math.sin(x * 0.05) * 12 + math.cos(x * 0.02) * 8)
        pygame.draw.polygon(screen, (20, 30, 45), [(x, pad_ground_y), (x + 12, pad_ground_y - h), (x + 24, pad_ground_y)])


def draw_cosmodrome(frame_count):
    draw_earth_sky(frame_count)

    beam_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.polygon(beam_surface, (255, 255, 220, 25), [(180, pad_ground_y), (rocket_x + 10, rocket_y + 20), (rocket_x + 20, rocket_y + 50), (195, pad_ground_y)])
    pygame.draw.polygon(beam_surface, (255, 255, 220, 25), [(620, pad_ground_y), (rocket_x + rocket_w - 10, rocket_y + 20), (rocket_x + rocket_w - 20, rocket_y + 50), (605, pad_ground_y)])
    screen.blit(beam_surface, (0, 0))

    tower_x = 70
    tower_w = 48
    tower_top_y = 180
    pygame.draw.rect(screen, TOWER_STEEL, (tower_x, tower_top_y, 8, pad_ground_y - tower_top_y))
    pygame.draw.rect(screen, TOWER_STEEL, (tower_x + tower_w - 8, tower_top_y, 8, pad_ground_y - tower_top_y))
    for ty in range(tower_top_y, pad_ground_y, 35):
        pygame.draw.rect(screen, TOWER_GRAY, (tower_x, ty, tower_w, 4))
        pygame.draw.line(screen, TOWER_GRAY, (tower_x, ty), (tower_x + tower_w, ty + 35), 2)
        pygame.draw.line(screen, TOWER_GRAY, (tower_x + tower_w, ty), (tower_x, ty + 35), 2)

    beacon_color = (255, 30, 30) if (frame_count // 25) % 2 == 0 else (100, 10, 10)
    pygame.draw.circle(screen, beacon_color, (tower_x + tower_w // 2, tower_top_y - 6), 5)
    pygame.draw.circle(screen, (255, 200, 200), (tower_x + tower_w // 2, tower_top_y - 6), 2)

    bridge_y = rocket_y + 54
    pygame.draw.rect(screen, TOWER_GRAY, (tower_x + tower_w - 8, bridge_y, rocket_x - (tower_x + tower_w) + 12, 6))
    pygame.draw.rect(screen, (220, 220, 230), (tower_x + tower_w - 8, bridge_y - 12, rocket_x - (tower_x + tower_w) + 12, 2))
    for bx in range(tower_x + tower_w, rocket_x, 15):
        pygame.draw.line(screen, (160, 160, 170), (bx, bridge_y - 12), (bx, bridge_y), 2)

    radar_x = 640
    pygame.draw.rect(screen, (60, 65, 75), (radar_x, pad_ground_y - 45, 55, 45))
    pygame.draw.rect(screen, (100, 110, 125), (radar_x, pad_ground_y - 45, 55, 45), width=2)
    pygame.draw.rect(screen, (100, 220, 255), (radar_x + 10, pad_ground_y - 35, 14, 10))
    pygame.draw.line(screen, (180, 180, 190), (radar_x + 28, pad_ground_y - 45), (radar_x + 28, pad_ground_y - 65), 3)
    pygame.draw.arc(screen, (220, 220, 230), (radar_x + 28 - 18, pad_ground_y - 80, 36, 25), 0.2, 2.9, 3)

    pad_table_rect = pygame.Rect(rocket_x - 30, pad_ground_y - 14, rocket_w + 60, 16)
    pygame.draw.rect(screen, CONCRETE_LIGHT, pad_table_rect)
    pygame.draw.rect(screen, (100, 105, 115), pad_table_rect, width=2)
    pygame.draw.rect(screen, (20, 20, 25), (rocket_x + 6, pad_ground_y - 14, rocket_w - 12, 16))

    pygame.draw.line(screen, (140, 140, 150), (rocket_x - 12, pad_ground_y - 14), (rocket_x - 2, rocket_y + rocket_h - 15), 4)
    pygame.draw.line(screen, (140, 140, 150), (rocket_x + rocket_w + 12, pad_ground_y - 14), (rocket_x + rocket_w + 2, rocket_y + rocket_h - 15), 4)

    pygame.draw.rect(screen, CONCRETE_DARK, (0, pad_ground_y, WIDTH, HEIGHT - pad_ground_y))
    pygame.draw.line(screen, CONCRETE_LIGHT, (0, pad_ground_y), (WIDTH, pad_ground_y), 4)

    stripe_w = 16
    for sx in range(0, WIDTH, stripe_w * 2):
        pygame.draw.polygon(screen, YELLOW_HAZARD, [(sx, pad_ground_y), (sx + stripe_w, pad_ground_y), (sx + stripe_w - 6, pad_ground_y + 8), (sx - 6, pad_ground_y + 8)])
        pygame.draw.polygon(screen, BLACK_HAZARD, [(sx + stripe_w, pad_ground_y), (sx + stripe_w * 2, pad_ground_y), (sx + stripe_w * 2 - 6, pad_ground_y + 8), (sx + stripe_w - 6, pad_ground_y + 8)])


def draw_earth_in_space():
    ex, ey, er = 680, 95, 38
    glow_surf = pygame.Surface((er * 2 + 16, er * 2 + 16), pygame.SRCALPHA)
    pygame.draw.circle(glow_surf, (80, 160, 255, 45), (er + 8, er + 8), er + 4)
    screen.blit(glow_surf, (ex - er - 8, ey - er - 8))

    earth_surf = pygame.Surface((er * 2, er * 2), pygame.SRCALPHA)
    pygame.draw.circle(earth_surf, (30, 85, 195), (er, er), er)
    pygame.draw.circle(earth_surf, (45, 140, 75), (er - 10, er - 8), 15)
    pygame.draw.circle(earth_surf, (45, 140, 75), (er + 12, er + 10), 14)
    pygame.draw.circle(earth_surf, (40, 125, 65), (er - 2, er + 14), 10)

    pygame.draw.ellipse(earth_surf, (240, 245, 255, 200), (er - 16, er - 14, 22, 9))
    pygame.draw.ellipse(earth_surf, (240, 245, 255, 180), (er - 4, er + 2, 26, 8))

    shadow_surf = pygame.Surface((er * 2, er * 2), pygame.SRCALPHA)
    for sx in range(er, er * 2):
        alpha = int(190 * ((sx - er) / er))
        pygame.draw.line(shadow_surf, (15, 15, 25, alpha), (sx, 0), (sx, er * 2))

    mask_surf = pygame.Surface((er * 2, er * 2), pygame.SRCALPHA)
    pygame.draw.circle(mask_surf, (255, 255, 255, 255), (er, er), er)
    shadow_surf.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

    earth_surf.blit(shadow_surf, (0, 0))
    screen.blit(earth_surf, (ex - er, ey - er))


def draw_moon_surface(frame_count):
    for s in space_stars:
        brightness = 180 + int(60 * math.sin(frame_count * 0.05 + s['x']))
        pygame.draw.circle(screen, (brightness, brightness, brightness), (int(s['x']), int(s['y'])), s['r'])

    draw_earth_in_space()

    pygame.draw.rect(screen, (100, 100, 110), (0, lunar_ground_y, WIDTH, HEIGHT - lunar_ground_y))
    pygame.draw.line(screen, (150, 150, 165), (0, lunar_ground_y), (WIDTH, lunar_ground_y), 3)

    for cx, cy, rx, ry in craters:
        pygame.draw.ellipse(screen, (65, 65, 75), (cx - rx, cy - ry, rx * 2, ry * 2))
        pygame.draw.ellipse(screen, (130, 130, 145), (cx - rx, cy - ry, rx * 2, ry * 2), width=2)

    pad_rect = pygame.Rect(WIDTH // 2 - 60, lunar_ground_y - 8, 120, 10)
    pygame.draw.rect(screen, (130, 130, 140), pad_rect)
    pygame.draw.rect(screen, (180, 180, 190), pad_rect, width=2)

    light_color = (255, 60, 60) if (frame_count // 30) % 2 == 0 else (255, 220, 0)
    pygame.draw.circle(screen, light_color, (WIDTH // 2 - 50, lunar_ground_y - 4), 3)
    pygame.draw.circle(screen, light_color, (WIDTH // 2 + 50, lunar_ground_y - 4), 3)


def draw_flag(x, y):
    pygame.draw.line(screen, (220, 220, 230), (x, y), (x, y - 56), 3)
    flag_rect = (x, y - 56, 32, 20)
    pygame.draw.rect(screen, (210, 30, 30), flag_rect)
    pygame.draw.circle(screen, (255, 215, 0), (x + 9, y - 46), 4)


def draw_cosmonaut(x, y, frame_count, is_walking=False, waving=False, facing_right=True):
    backpack_x = x - 6 if facing_right else x + 16
    pygame.draw.rect(screen, (180, 180, 195), (backpack_x, y + 10, 7, 18))
    pygame.draw.rect(screen, (70, 70, 80), (backpack_x, y + 10, 7, 18), width=1)

    pygame.draw.rect(screen, WHITE, (x, y + 10, 17, 16))
    pygame.draw.rect(screen, (60, 60, 70), (x, y + 10, 17, 16), width=1)

    pygame.draw.rect(screen, (220, 40, 40), (x + 2, y + 14, 13, 3))
    pygame.draw.circle(screen, (70, 160, 240), (x + 5, y + 21), 2)
    pygame.draw.circle(screen, (255, 200, 40), (x + 11, y + 21), 2)

    helmet_cx = x + 8
    helmet_cy = y + 7
    pygame.draw.circle(screen, WHITE, (helmet_cx, helmet_cy), 8)
    pygame.draw.circle(screen, (60, 60, 70), (helmet_cx, helmet_cy), 8, width=1)

    visor_x = x + 6 if facing_right else x + 2
    pygame.draw.rect(screen, CYAN_GLASS, (visor_x, y + 4, 8, 6))
    pygame.draw.rect(screen, (50, 80, 100), (visor_x, y + 4, 8, 6), width=1)
    pygame.draw.line(screen, (255, 255, 255), (visor_x + 1, y + 5), (visor_x + 3, y + 5), 1)

    if waving:
        arm_wave_offset = int(math.sin(frame_count * 0.3) * 4)
        pygame.draw.line(screen, WHITE, (x + 8, y + 12), (x + 18, y - 6 + arm_wave_offset), 4)
        pygame.draw.circle(screen, (220, 40, 40), (x + 18, y - 6 + arm_wave_offset), 3)
    else:
        arm_offset = int(math.sin(frame_count * 0.25) * 4) if is_walking else 0
        pygame.draw.line(screen, WHITE, (x + 8, y + 12), (x + 8 + arm_offset, y + 22), 4)
        pygame.draw.circle(screen, (220, 40, 40), (x + 8 + arm_offset, y + 23), 2)

    if is_walking:
        step = int(math.sin(frame_count * 0.3) * 5)
        pygame.draw.line(screen, WHITE, (x + 4, y + 26), (x + 4 - step, y + 34), 4)
        pygame.draw.rect(screen, (70, 70, 80), (x + 2 - step, y + 33, 5, 3))
        pygame.draw.line(screen, WHITE, (x + 13, y + 26), (x + 13 + step, y + 34), 4)
        pygame.draw.rect(screen, (70, 70, 80), (x + 11 + step, y + 33, 5, 3))
    else:
        pygame.draw.line(screen, WHITE, (x + 4, y + 26), (x + 4, y + 34), 4)
        pygame.draw.rect(screen, (70, 70, 80), (x + 2, y + 33, 5, 3))
        pygame.draw.line(screen, WHITE, (x + 13, y + 26), (x + 13, y + 34), 4)
        pygame.draw.rect(screen, (70, 70, 80), (x + 11, y + 33, 5, 3))


def draw_lunokhod(x, y, facing_right=True):
    # Корпус Лунохода (форма перевернутой усеченной чаши)
    pygame.draw.rect(screen, (200, 205, 215), (x + 6, y + 10, rover_w - 12, 14))
    pygame.draw.polygon(screen, (170, 175, 185), [(x + 6, y + 10), (x + 2, y + 4), (x + rover_w - 2, y + 4), (x + rover_w - 6, y + 10)])
    pygame.draw.rect(screen, (60, 65, 75), (x + 6, y + 10, rover_w - 12, 14), width=1)

    # Солнечная панель (открытая крышка сверху)
    panel_angle_x = x - 6 if facing_right else x + rover_w - 10
    pygame.draw.polygon(screen, (40, 70, 130), [(panel_angle_x, y - 4), (panel_angle_x + 22, y - 4), (x + 18, y + 4), (x + 6, y + 4)])
    pygame.draw.polygon(screen, (100, 160, 240), [(panel_angle_x, y - 4), (panel_angle_x + 22, y - 4), (x + 18, y + 4), (x + 6, y + 4)], width=1)

    # Остронаправленная спиральная антенна
    ant_x = x + rover_w - 12 if facing_right else x + 12
    pygame.draw.line(screen, (220, 220, 230), (ant_x, y + 4), (ant_x, y - 14), 2)
    pygame.draw.circle(screen, (255, 215, 0), (ant_x, y - 14), 3)

    # Телевизионные камеры (два иллюминатора спереди)
    cam_x = x + rover_w - 8 if facing_right else x + 4
    pygame.draw.circle(screen, (30, 30, 40), (cam_x, y + 14), 3)
    pygame.draw.circle(screen, CYAN_GLASS, (cam_x, y + 14), 2)

    # 8 сетчатых титановых колёс (по 4 с каждой видимой стороны)
    for i in range(4):
        wx = x + 6 + i * 11
        pygame.draw.circle(screen, (80, 85, 95), (wx, y + 26), 5)
        pygame.draw.circle(screen, (180, 185, 195), (wx, y + 26), 2)


def draw_rocket(x, y, is_thrusting=False, deploy_legs=False, hatch_open=False):
    if deploy_legs:
        pygame.draw.line(screen, (160, 160, 170), (x - 6, y + rocket_h - 14), (x - 18, y + rocket_h + 8), 3)
        pygame.draw.line(screen, (120, 120, 130), (x - 24, y + rocket_h + 8), (x - 12, y + rocket_h + 8), 3)
        pygame.draw.line(screen, (160, 160, 170), (x + rocket_w + 6, y + rocket_h - 14), (x + rocket_w + 18, y + rocket_h + 8), 3)
        pygame.draw.line(screen, (120, 120, 130), (x + rocket_w + 12, y + rocket_h + 8), (x + rocket_w + 24, y + rocket_h + 8), 3)

    pygame.draw.rect(screen, (200, 200, 210), (x - 8, y + 36, 10, 48))
    pygame.draw.polygon(screen, RED_ACCENT, [(x - 8, y + 36), (x - 3, y + 28), (x + 2, y + 36)])
    pygame.draw.rect(screen, (200, 200, 210), (x + rocket_w - 2, y + 36, 10, 48))
    pygame.draw.polygon(screen, RED_ACCENT, [(x + rocket_w - 2, y + 36), (x + rocket_w + 3, y + 28), (x + rocket_w + 8, y + 36)])

    pygame.draw.rect(screen, WHITE, (x, y + 18, rocket_w, rocket_h - 26))
    pygame.draw.rect(screen, (70, 70, 80), (x, y + 18, rocket_w, rocket_h - 26), width=1)

    nose = [(x + rocket_w // 2, y), (x, y + 18), (x + rocket_w, y + 18)]
    pygame.draw.polygon(screen, RED_NOSE, nose)
    pygame.draw.polygon(screen, (70, 70, 80), nose, width=1)

    pygame.draw.rect(screen, RED_ACCENT, (x, y + 26, rocket_w, 3))
    pygame.draw.rect(screen, RED_ACCENT, (x, y + rocket_h - 20, rocket_w, 3))

    pygame.draw.circle(screen, (70, 70, 80), (x + rocket_w // 2, y + 36), 6)
    pygame.draw.circle(screen, CYAN_GLASS, (x + rocket_w // 2, y + 36), 4)

    hatch_color = (60, 180, 80) if hatch_open else (90, 90, 100)
    pygame.draw.rect(screen, hatch_color, (x + 8, y + 54, 16, 22))
    pygame.draw.rect(screen, (50, 50, 60), (x + 8, y + 54, 16, 22), width=1)

    font_soiuz = pygame.font.SysFont("Arial", 8, bold=True)
    text_soiuz = font_soiuz.render("СОЮЗ М", True, (40, 40, 50))
    screen.blit(text_soiuz, (x + 25, y + 60))

    pygame.draw.rect(screen, (70, 70, 80), (x + 8, y + rocket_h - 8, rocket_w - 16, 8))

    if is_thrusting:
        flame_len = random.randint(30, 44) if state in ["SPACE_ARCADE", "FLYING_UP"] else 18
        pygame.draw.polygon(screen, (255, 140, 0), [(x + 8, y + rocket_h), (x + rocket_w - 8, y + rocket_h), (x + rocket_w // 2, y + rocket_h + flame_len)])
        pygame.draw.polygon(screen, (255, 215, 0), [(x + 14, y + rocket_h), (x + rocket_w - 14, y + rocket_h), (x + rocket_w // 2, y + rocket_h + int(flame_len * 0.6))])


def draw_dendy_text(text, center_x, center_y, size=64, color=TEXT_COLOR):
    font = pygame.font.SysFont("Arial", size, bold=True)
    shadow_surf = font.render(text, True, TEXT_SHADOW)
    screen.blit(shadow_surf, shadow_surf.get_rect(center=(center_x + 2, center_y + 2)))
    text_surf = font.render(text, True, color)
    screen.blit(text_surf, text_surf.get_rect(center=(center_x, center_y)))


def draw_hud():
    # Панель приборов вверху
    pygame.draw.rect(screen, (25, 30, 40), (0, 0, WIDTH, 34))
    pygame.draw.line(screen, (60, 70, 90), (0, 34), (WIDTH, 34), 2)

    font_hud = pygame.font.SysFont("Arial", 14, bold=True)
    txt_dist = font_hud.render(f"ДИСТАНЦИЯ К ЛУНЕ: {int(mission_distance)}%", True, (130, 220, 255))
    screen.blit(txt_dist, (15, 8))

    txt_score = font_hud.render(f"КРИСТАЛЛЫ: {score} ✦", True, GOLD)
    screen.blit(txt_score, (320, 8))

    # Шкала топлива
    txt_fuel = font_hud.render("ТОПЛИВО:", True, (240, 240, 250))
    screen.blit(txt_fuel, (550, 8))
    pygame.draw.rect(screen, (60, 60, 70), (635, 10, 140, 14))
    fuel_color = (60, 220, 100) if fuel > 35 else (240, 60, 60)
    pygame.draw.rect(screen, fuel_color, (635, 10, int(140 * (max(0, fuel) / 100.0)), 14))
    pygame.draw.rect(screen, (180, 180, 190), (635, 10, 140, 14), width=1)


async def main():
    global state, countdown_timer, mission_distance, score, fuel, clock, FPS
    global rocket_x, rocket_y, rocket_vx, rocket_vy
    global cosmo_x, cosmo_y, cosmo_waving_timer, rover_x, rover_y, rover_in_use
    global frame_count, running

    frame_count = 0
    running = True
    while running:
        clock.tick(FPS)
        frame_count += 1
        screen.fill(BLACK_HAZARD)

        keys = pygame.key.get_pressed()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and state == "EARTH_READY":
                    state = "COSMO_WALKING"
                    play_sfx(snd_beep)
                elif event.key == pygame.K_r and state in ["LUNAR_ROAMING", "LANDED"]:
                    state = "EARTH_READY"
                    rocket_x = WIDTH // 2 - rocket_w // 2
                    rocket_y = pad_ground_y - rocket_h + 10
                    rocket_vx = 0.0
                    rocket_vy = 0.0
                    cosmo_x = 130
                    cosmo_y = pad_ground_y - cosmo_h
                    rover_in_use = False
                    mission_distance = 0.0
                    score = 0
                    fuel = 100.0
                    particles.clear()
                    steam_particles.clear()
                    asteroids.clear()
                    crystals.clear()
                    fireworks.clear()

        # === ЛОГИКА СОСТОЯНИЙ ===
        if state == "EARTH_READY":
            draw_cosmodrome(frame_count)

            if random.random() < 0.25:
                steam_particles.append({
                    'x': rocket_x + 10 + random.choice([0, rocket_w - 20]),
                    'y': rocket_y + 35,
                    'vx': random.uniform(-0.8, -0.2) if random.random() < 0.5 else random.uniform(0.2, 0.8),
                    'vy': random.uniform(-0.6, -0.1),
                    'r': random.randint(2, 4),
                    'alpha': 180
                })

            for s in steam_particles:
                s['x'] += s['vx']
                s['y'] += s['vy']
                s['alpha'] -= 3
                if s['alpha'] > 0:
                    steam_surf = pygame.Surface((s['r']*2, s['r']*2), pygame.SRCALPHA)
                    pygame.draw.circle(steam_surf, (220, 235, 255, s['alpha']), (s['r'], s['r']), s['r'])
                    screen.blit(steam_surf, (int(s['x']), int(s['y'])))
            steam_particles = [s for s in steam_particles if s['alpha'] > 0]

            draw_rocket(rocket_x, rocket_y, is_thrusting=False, deploy_legs=False, hatch_open=True)
            draw_cosmonaut(cosmo_x, cosmo_y, frame_count, is_walking=False, waving=False, facing_right=True)
            draw_dendy_text("НАЖМИТЕ ПРОБЕЛ — ПОСАДКА И ПУСК!", WIDTH // 2, 60, size=24, color=(240, 240, 255))

        elif state == "COSMO_WALKING":
            draw_cosmodrome(frame_count)
            hatch_target_x = rocket_x + 8

            if cosmo_x < hatch_target_x:
                cosmo_x += cosmo_speed
                if frame_count % 14 == 0:
                    play_sfx(snd_step)
                draw_cosmonaut(cosmo_x, cosmo_y, frame_count, is_walking=True, waving=False, facing_right=True)
                draw_rocket(rocket_x, rocket_y, is_thrusting=False, deploy_legs=False, hatch_open=True)
            else:
                cosmo_waving_timer += 1
                draw_rocket(rocket_x, rocket_y, is_thrusting=False, deploy_legs=False, hatch_open=True)
                draw_cosmonaut(cosmo_x, cosmo_y, frame_count, is_walking=False, waving=True, facing_right=True)
                draw_dendy_text("ПОСАДКА В РАКЕТУ...", WIDTH // 2, 60, size=24, color=(255, 215, 0))

                if cosmo_waving_timer > 60:
                    state = "COUNTDOWN"
                    countdown_timer = 90
                    cosmo_waving_timer = 0
                    play_sfx(snd_beep)

        elif state == "COUNTDOWN":
            draw_cosmodrome(frame_count)
            countdown_timer -= 1
            draw_rocket(rocket_x, rocket_y, is_thrusting=False, deploy_legs=False, hatch_open=False)

            if random.random() < 0.8:
                for _ in range(2):
                    particles.append({
                        'x': rocket_x + rocket_w // 2 + random.randint(-20, 20),
                        'y': rocket_y + rocket_h - 4,
                        'vx': random.uniform(-2.5, 2.5),
                        'vy': random.uniform(0.2, 1.5),
                        'r': random.randint(4, 10),
                        'life': 35
                    })

            for p in particles:
                if p['life'] > 0:
                    p['x'] += p['vx']
                    p['y'] += p['vy']
                    p['life'] -= 1
                    pygame.draw.circle(screen, (160, 160, 170), (int(p['x']), int(p['y'])), p['r'])

            sec = (countdown_timer // 30) + 1
            if sec > 1:
                draw_dendy_text(f"ЗАПУСК ЧЕРЕЗ: {sec}", WIDTH // 2, 60, size=28, color=(255, 140, 0))
                if countdown_timer % 30 == 0:
                    play_sfx(snd_beep)
            else:
                draw_dendy_text("ПОЕХАЛИ! ПУСК!", WIDTH // 2, 60, size=36, color=(255, 60, 60))
                if countdown_timer == 29:
                    play_sfx(snd_launch)

            if countdown_timer <= 0:
                state = "SPACE_ARCADE"
                particles.clear()
                rocket_x = WIDTH // 2 - rocket_w // 2
                rocket_y = HEIGHT - 140

        elif state == "SPACE_ARCADE":
            # Космический полёт сквозь астероиды
            for s in space_stars:
                s['y'] += s['speed']
                if s['y'] > HEIGHT:
                    s['y'] = 0
                    s['x'] = random.randint(0, WIDTH)
                pygame.draw.circle(screen, (220, 220, 240), (int(s['x']), int(s['y'])), s['r'])

            # Управление ракетой в космосе
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                rocket_x -= 5
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                rocket_x += 5
            rocket_x = max(20, min(WIDTH - rocket_w - 20, rocket_x))

            # Генерация астероидов
            if random.random() < 0.04 and len(asteroids) < 5:
                asteroids.append({
                    'x': random.randint(40, WIDTH - 80),
                    'y': -40,
                    'r': random.randint(16, 26),
                    'speed': random.uniform(3.0, 5.0),
                    'rot': random.uniform(0, 360)
                })

            # Генерация кристаллов
            if random.random() < 0.03 and len(crystals) < 4:
                crystals.append({
                    'x': random.randint(50, WIDTH - 70),
                    'y': -30,
                    'speed': 3.5
                })

            # Отрисовка и движение астероидов
            for a in asteroids[:]:
                a['y'] += a['speed']
                pygame.draw.circle(screen, (110, 105, 115), (int(a['x']), int(a['y'])), a['r'])
                pygame.draw.circle(screen, (70, 65, 75), (int(a['x']), int(a['y'])), a['r'], width=2)
                pygame.draw.circle(screen, (80, 75, 85), (int(a['x'] - 4), int(a['y'] - 3)), a['r'] // 3)

                # Проверка столкновения
                rocket_rect = pygame.Rect(rocket_x, rocket_y, rocket_w, rocket_h)
                if rocket_rect.collidepoint(a['x'], a['y']):
                    fuel = max(0.0, fuel - 0.4)  # трата топлива при задевании

                if a['y'] > HEIGHT + 50:
                    asteroids.remove(a)

            # Отрисовка кристаллов
            for c in crystals[:]:
                c['y'] += c['speed']
                cx, cy = int(c['x']), int(c['y'])
                # Золотой ромб кристалла
                pts = [(cx, cy - 8), (cx + 7, cy), (cx, cy + 8), (cx - 7, cy)]
                pygame.draw.polygon(screen, GOLD, pts)
                pygame.draw.polygon(screen, WHITE, pts, width=1)

                rocket_rect = pygame.Rect(rocket_x, rocket_y, rocket_w, rocket_h)
                if rocket_rect.collidepoint(cx, cy):
                    score += 10
                    play_sfx(snd_coin)
                    crystals.remove(c)
                elif c['y'] > HEIGHT + 40:
                    crystals.remove(c)

            draw_rocket(rocket_x, rocket_y, is_thrusting=True, deploy_legs=False, hatch_open=False)

            # Прогресс полета
            mission_distance += 0.25
            draw_hud()

            if mission_distance >= 100.0:
                state = "LUNAR_LANDING"
                rocket_x = WIDTH // 2 - rocket_w // 2
                rocket_y = -rocket_h
                rocket_vy = 1.0
                asteroids.clear()
                crystals.clear()

        elif state == "LUNAR_LANDING":
            # Ручная посадка на Луну (Lunar Lander)
            draw_moon_surface(frame_count)

            is_thrust = False
            if (keys[pygame.K_UP] or keys[pygame.K_SPACE] or keys[pygame.K_w]) and fuel > 0:
                rocket_vy -= 0.12
                fuel = max(0.0, fuel - 0.18)
                is_thrust = True

            if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and fuel > 0:
                rocket_vx -= 0.08
                fuel = max(0.0, fuel - 0.05)
            if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and fuel > 0:
                rocket_vx += 0.08
                fuel = max(0.0, fuel - 0.05)

            # Гравитация Луны
            rocket_vy += 0.04
            rocket_x += rocket_vx
            rocket_y += rocket_vy
            rocket_vx *= 0.98

            rocket_x = max(20, min(WIDTH - rocket_w - 20, rocket_x))

            target_land_y = lunar_ground_y - rocket_h - 6
            deploy_legs = (rocket_y > 150)

            draw_rocket(int(rocket_x), int(rocket_y), is_thrusting=is_thrust, deploy_legs=deploy_legs, hatch_open=False)
            draw_hud()

            draw_dendy_text("РУЧНАЯ ПОСАДКА: [ПРОБЕЛ / СТРЕЛКИ]", WIDTH // 2, 60, size=20, color=(160, 230, 255))

            if rocket_y >= target_land_y:
                rocket_y = target_land_y
                state = "ROVER_DEPLOY"
                play_sfx(snd_pop)
                # Начальные координаты Лунохода и космонавта
                rover_x = rocket_x + rocket_w + 10
                rover_y = lunar_ground_y - rover_h + 2
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

        elif state in ["ROVER_DEPLOY", "LUNAR_ROAMING"]:
            draw_moon_surface(frame_count)

            # Оседание пыли
            for p in particles:
                if p['life'] > 0:
                    p['x'] += p['vx']
                    p['y'] += p['vy']
                    p['life'] -= 1
                    pygame.draw.circle(screen, (160, 160, 175), (int(p['x']), int(p['y'])), p['r'])

            draw_rocket(rocket_x, int(rocket_y), is_thrusting=False, deploy_legs=True, hatch_open=True)

            # Выдвижной пандус из ракеты для Лунохода
            pygame.draw.line(screen, (180, 185, 195), (rocket_x + rocket_w - 6, rocket_y + rocket_h - 12), (rocket_x + rocket_w + 24, lunar_ground_y), 4)

            # Установленный флаг
            draw_flag(rocket_x - 45, lunar_ground_y - 4)

            if state == "ROVER_DEPLOY":
                # Космонавт выходит и идет к Луноходу
                if cosmo_x < rover_x + 12:
                    cosmo_x += 1.2
                    draw_cosmonaut(cosmo_x, cosmo_y, frame_count, is_walking=True, waving=False, facing_right=True)
                    draw_lunokhod(rover_x, rover_y, facing_right=True)
                    draw_dendy_text("ВЫГРУЗКА ЛУНОХОДА-1...", WIDTH // 2, 60, size=24, color=(100, 240, 130))
                else:
                    state = "LUNAR_ROAMING"
                    rover_in_use = True
                    play_sfx(snd_coin)

            elif state == "LUNAR_ROAMING":
                # Управление Луноходом по лунной поверхности!
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    rover_x -= 3
                    facing = False
                elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    rover_x += 3
                    facing = True
                else:
                    facing = True

                rover_x = max(20, min(WIDTH - rover_w - 20, rover_x))
                draw_lunokhod(rover_x, rover_y, facing_right=facing)
                # Космонавт сидит в Луноходе
                draw_cosmonaut(rover_x + 16, rover_y - 12, frame_count, is_walking=False, waving=True, facing_right=facing)

                # Праздничный салют над Луной!
                if random.random() < 0.08:
                    fx = random.randint(80, WIDTH - 80)
                    fy = random.randint(60, 240)
                    f_color = random.choice([(255, 80, 80), (255, 220, 50), (80, 220, 255), (100, 255, 120), (255, 120, 240)])
                    for _ in range(18):
                        ang = random.uniform(0, math.pi * 2)
                        spd = random.uniform(1.2, 4.0)
                        fireworks.append({
                            'x': fx,
                            'y': fy,
                            'vx': math.cos(ang) * spd,
                            'vy': math.sin(ang) * spd,
                            'color': f_color,
                            'life': random.randint(20, 40)
                        })
                    play_sfx(snd_pop)

                for fw in fireworks[:]:
                    fw['x'] += fw['vx']
                    fw['y'] += fw['vy']
                    fw['life'] -= 1
                    if fw['life'] > 0:
                        pygame.draw.circle(screen, fw['color'], (int(fw['x']), int(fw['y'])), 2)
                    else:
                        fireworks.remove(fw)

                # Победные титры
                draw_dendy_text("СОЮЗ-М & ЛУНОХОД-1", WIDTH // 2, HEIGHT // 2 - 80, size=52, color=(255, 215, 0))
                draw_dendy_text("МИССИЯ УСПЕШНО ВЫПОЛНЕНА!", WIDTH // 2, HEIGHT // 2 - 20, size=28, color=(100, 240, 130))
                draw_dendy_text(f"СОБРАНО КРИСТАЛЛОВ: {score} ✦", WIDTH // 2, HEIGHT // 2 + 25, size=22, color=GOLD)
                draw_dendy_text("УПРАВЛЕНИЕ ЛУНОХОДОМ: [← / →]  |  [R] - ПОВТОР", WIDTH // 2, HEIGHT // 2 + 65, size=18, color=(200, 200, 220))

            pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())
