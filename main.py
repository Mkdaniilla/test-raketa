import pygame
import sys

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ракета 'Союз-М' — пиксель-арт")

# Цвета
BLACK = (20, 20, 30)
BRICK_COLOR = (100, 60, 40)
ACCENT = (180, 120, 80)

# Ракетка «Союз-М»
RED_NOSE = (225, 40, 40)
RED_ACCENT = (195, 30, 30)
CYAN_GLASS = (130, 220, 250)

# Текст
TEXT_COLOR = (255, 215, 0)  # золотисто‑жёлтый
TEXT_SHADOW = (30, 30, 40)  # тень

# Параметры ракетки
rocket_w = 46
rocket_h = 96
rocket_x = WIDTH // 2 - rocket_w // 2
rocket_y = HEIGHT - rocket_h - 10
rocket_speed = 4

# Кубики
cube_size = 40

# Платформы
platforms = []
for x in range(0, WIDTH, cube_size):
    platforms.append(pygame.Rect(x, HEIGHT - cube_size, cube_size, cube_size))
for y in range(0, HEIGHT - cube_size * 2, cube_size):
    platforms.append(pygame.Rect(0, y, cube_size, cube_size))
    platforms.append(pygame.Rect(WIDTH - cube_size, y, cube_size, cube_size))
platforms.append(pygame.Rect(200, 400, cube_size * 2, cube_size))
platforms.append(pygame.Rect(500, 300, cube_size * 2, cube_size))

# Состояние
is_flying = False
show_end_text = False
clock = pygame.time.Clock()
FPS = 60


def draw_rocket(x, y):
    # 1. Боковые ускорители (левый и правый)
    pygame.draw.rect(screen, (200, 200, 210), (x - 8, y + 36, 10, 48))
    pygame.draw.polygon(screen, RED_ACCENT, [(x - 8, y + 36), (x - 3, y + 28), (x + 2, y + 36)])
    pygame.draw.rect(screen, (200, 200, 210), (x + rocket_w - 2, y + 36, 10, 48))
    pygame.draw.polygon(screen, RED_ACCENT, [(x + rocket_w - 2, y + 36), (x + rocket_w + 3, y + 28), (x + rocket_w + 8, y + 36)])

    # 2. Белый корпус
    pygame.draw.rect(screen, (245, 245, 250), (x, y + 18, rocket_w, rocket_h - 26))
    pygame.draw.rect(screen, (70, 70, 80), (x, y + 18, rocket_w, rocket_h - 26), width=1)

    # 3. Красный колпачок (носовой обтекатель)
    nose = [(x + rocket_w // 2, y), (x, y + 18), (x + rocket_w, y + 18)]
    pygame.draw.polygon(screen, RED_NOSE, nose)
    pygame.draw.polygon(screen, (70, 70, 80), nose, width=1)

    # 4. Красные полосы
    pygame.draw.rect(screen, RED_ACCENT, (x, y + 26, rocket_w, 3))
    pygame.draw.rect(screen, RED_ACCENT, (x, y + rocket_h - 20, rocket_w, 3))

    # 5. Иллюминатор
    pygame.draw.circle(screen, (70, 70, 80), (x + rocket_w // 2, y + 36), 6)
    pygame.draw.circle(screen, CYAN_GLASS, (x + rocket_w // 2, y + 36), 4)

    # 6. Надпись "СОЮЗ М" на борту ракеты
    font_soiuz = pygame.font.SysFont("Arial", 9, bold=True)
    text_soiuz = font_soiuz.render("СОЮЗ М", True, (40, 40, 50))
    screen.blit(text_soiuz, text_soiuz.get_rect(center=(x + rocket_w // 2, y + 50)))

    # 7. Сопла двигателей
    pygame.draw.rect(screen, (70, 70, 80), (x + 8, y + rocket_h - 8, rocket_w - 16, 8))

    # 8. Пламя при старте
    if is_flying:
        pygame.draw.polygon(screen, (255, 140, 0), [(x + 8, y + rocket_h), (x + rocket_w - 8, y + rocket_h), (x + rocket_w // 2, y + rocket_h + 35)])
        pygame.draw.polygon(screen, (255, 215, 0), [(x + 14, y + rocket_h), (x + rocket_w - 14, y + rocket_h), (x + rocket_w // 2, y + rocket_h + 22)])


def draw_platforms():
    for platform in platforms:
        pygame.draw.rect(screen, BRICK_COLOR, platform)
        pygame.draw.rect(screen, ACCENT, platform, width=2)
        half = cube_size // 2
        pygame.draw.line(screen, ACCENT, (platform.x, platform.y + half), (platform.x + half, platform.y + half), 1)
        pygame.draw.line(screen, ACCENT, (platform.x + half, platform.y), (platform.x + half, platform.y + half), 1)


def draw_dendy_text(text, center_x, center_y, size=64):
    font = pygame.font.SysFont("Arial", size, bold=True)

    # Тень (ровно 2 пикселя вниз‑вправо от центра)
    shadow_surf = font.render(text, True, TEXT_SHADOW)
    shadow_rect = shadow_surf.get_rect(center=(center_x + 2, center_y + 2))
    screen.blit(shadow_surf, shadow_rect)

    # Основной текст (ровно по центру)
    text_surf = font.render(text, True, TEXT_COLOR)
    text_rect = text_surf.get_rect(center=(center_x, center_y))
    screen.blit(text_surf, text_rect)


running = True
while running:
    clock.tick(FPS)
    screen.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not is_flying and not show_end_text:
                is_flying = True
            elif event.key == pygame.K_r and show_end_text:
                is_flying = False
                show_end_text = False
                rocket_y = HEIGHT - rocket_h - 10

    # Логика полёта
    if is_flying and rocket_y > -rocket_h:
        rocket_y -= rocket_speed
    elif is_flying and rocket_y <= -rocket_h:
        is_flying = False
        show_end_text = True

    draw_platforms()
    draw_rocket(rocket_x, rocket_y)

    if show_end_text:
        draw_dendy_text("СОЮЗ-М", WIDTH // 2, HEIGHT // 2, size=70)

    pygame.display.flip()

pygame.quit()
sys.exit()
