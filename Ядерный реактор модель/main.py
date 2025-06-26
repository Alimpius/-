import pygame
import random
import math
from enum import Enum

# Настройки
CELL_SIZE = 24
GRID_WIDTH = 40
GRID_HEIGHT = 21
PANEL_HEIGHT = 60
SCREEN_WIDTH = GRID_WIDTH * CELL_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * CELL_SIZE + PANEL_HEIGHT
FPS = 60
INITIAL_NEUTRONS = 100
MAX_PARTICLES = 1000

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (180, 180, 180)
ROD_COLOR = (30, 30, 30)
BG_COLOR = (220, 220, 220)
BLUE = (0, 100, 255, 100)
URANIUM_COLOR = (8, 60, 0)
XENON_COLOR = (100, 0, 100)
FAST_NEUTRON_COLOR = (255, 0, 0)
THERMAL_NEUTRON_COLOR = (40, 40, 40)
BUTTON_COLOR = (100, 100, 200)
BUTTON_HOVER_COLOR = (120, 120, 220)
NEUTRON_BUTTON_COLOR = (200, 100, 100)
NEUTRON_BUTTON_HOVER_COLOR = (220, 120, 120)
REACTOR_BG = (0, 255, 255)


# Типы частиц
class ParticleType(Enum):
    FAST_NEUTRON = 1
    THERMAL_NEUTRON = 2
    XENON = 3
    URANIUM = 4


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Ядерный реактор")
clock = pygame.time.Clock()

# Создаем поверхность для фона реактора с прозрачностью
reactor_bg = pygame.Surface((SCREEN_WIDTH, GRID_HEIGHT * CELL_SIZE), pygame.SRCALPHA)
reactor_bg.fill(REACTOR_BG)

# Структура стержней
uranium_lines = [x for x in range(0, GRID_WIDTH, 4)]
rod_columns = [x + 2 for x in uranium_lines if x + 2 < GRID_WIDTH]
rod_depths = {col: GRID_HEIGHT // 2 for col in rod_columns}

# Состояние паузы
paused = False

# Кнопки
pause_button_rect = pygame.Rect(SCREEN_WIDTH - 110, 10, 100, 30)
add_neutron_button_rect = pygame.Rect(SCREEN_WIDTH - 220, 10, 100, 30)


# Класс частиц
class Particle:
    def __init__(self, x, y, particle_type):
        self.x = x * CELL_SIZE + CELL_SIZE // 2
        self.y = y * CELL_SIZE + CELL_SIZE // 2

        # Инициализация движения для нейтронов
        if particle_type in [ParticleType.FAST_NEUTRON, ParticleType.THERMAL_NEUTRON]:
            angle = random.uniform(0, 2 * math.pi)
            self.vx = math.cos(angle)
            self.vy = math.sin(angle)
        else:
            self.vx = 0
            self.vy = 0

        # Настройки для разных типов частиц
        if particle_type == ParticleType.FAST_NEUTRON:
            self.speed = 4.0
            self.radius = CELL_SIZE // 8
            self.color = FAST_NEUTRON_COLOR
        elif particle_type == ParticleType.THERMAL_NEUTRON:
            self.speed = 1.5
            self.radius = CELL_SIZE // 8
            self.color = THERMAL_NEUTRON_COLOR
        elif particle_type == ParticleType.XENON:
            self.speed = 0.0
            self.radius = CELL_SIZE // 3
            self.color = XENON_COLOR
        elif particle_type == ParticleType.URANIUM:
            self.speed = 0.0
            self.radius = CELL_SIZE // 4
            self.color = URANIUM_COLOR

        self.type = particle_type
        self.active = True

    def distance_to(self, other):
        return math.hypot(self.x - other.x, self.y - other.y)

    def move(self, particles):
        if not self.active:
            return

        # Движение нейтронов
        if self.type in [ParticleType.FAST_NEUTRON, ParticleType.THERMAL_NEUTRON]:
            self.x += self.vx * self.speed
            self.y += self.vy * self.speed

            # Обработка границ реактора
            if self.x - self.radius < 0 or self.x + self.radius > SCREEN_WIDTH:
                self.vx = -self.vx
            if self.y - self.radius < 0 or self.y + self.radius > GRID_HEIGHT * CELL_SIZE:
                self.vy = -self.vy

            # Столкновение с ураном
            for p in particles:
                if p.active and p.type == ParticleType.URANIUM and self.distance_to(p) < self.radius + p.radius:
                    # Удаляем уран и нейтрон
                    self.active = False
                    p.active = False

                    # Создаем ксенон на месте урана
                    grid_x = int(p.x / CELL_SIZE)
                    grid_y = int(p.y / CELL_SIZE)
                    if len(particles) < MAX_PARTICLES:
                        particles.append(Particle(grid_x, grid_y, ParticleType.XENON))

                    # Создаем новые нейтроны с вероятностью 40%
                    if random.random() < 0.6:
                        for _ in range(3):
                            if len(particles) < MAX_PARTICLES:
                                new_n = Particle(grid_x, grid_y, ParticleType.THERMAL_NEUTRON)
                                angle = random.uniform(0, 2 * math.pi)
                                new_n.vx = math.cos(angle)
                                new_n.vy = math.sin(angle)
                                particles.append(new_n)
                    return

            # Столкновение быстрых нейтронов с ксеноном
            if self.type == ParticleType.FAST_NEUTRON:
                for p in particles:
                    if p.active and p.type == ParticleType.XENON and self.distance_to(p) < self.radius + p.radius:
                        if random.random() < 0.95:
                            p.active = False
                            self.active = False

                            particles.append(Particle(
                                random.randint(0, GRID_WIDTH - 1),
                                random.randint(0, GRID_HEIGHT - 1),
                                ParticleType.URANIUM
                            ))
                        return

            # Взаимодействие с управляющими стержнями
            for col in rod_columns:
                rod_x = col * CELL_SIZE
                rod_top = rod_depths[col] * CELL_SIZE
                if abs(self.x - rod_x) < self.radius + 2 and self.y < rod_top:
                    self.active = False
                    return

    def draw(self, surface):
        if self.active:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y + PANEL_HEIGHT)), self.radius)


# Инициализация частиц
particles = []

# Начальные нейтроны
for _ in range(INITIAL_NEUTRONS):
    particles.append(Particle(
        random.randint(0, GRID_WIDTH - 1),
        random.randint(0, GRID_HEIGHT - 1),
        ParticleType.FAST_NEUTRON
    ))

# Начальный уран (увеличили количество)
for _ in range(70):
    particles.append(Particle(
        random.randint(0, GRID_WIDTH - 1),
        random.randint(0, GRID_HEIGHT - 1),
        ParticleType.URANIUM
    ))


# Отрисовка
def draw():
    screen.fill(BG_COLOR)

    # Верхняя панель
    pygame.draw.rect(screen, (200, 200, 200), (0, 0, SCREEN_WIDTH, PANEL_HEIGHT))
    font = pygame.font.SysFont(None, 24)

    # Счетчики частиц
    n_fast = len([p for p in particles if p.type == ParticleType.FAST_NEUTRON and p.active])
    n_thermal = len([p for p in particles if p.type == ParticleType.THERMAL_NEUTRON and p.active])
    n_xenon = len([p for p in particles if p.type == ParticleType.XENON and p.active])
    n_uranium = len([p for p in particles if p.type == ParticleType.URANIUM and p.active])

    # Отображение статистики
    text = font.render(f"Быстрые: {n_fast} | Тепловые: {n_thermal} | Всего: {n_fast + n_thermal}", True, BLACK)
    screen.blit(text, (10, 10))

    text2 = font.render(f"Ксенон: {n_xenon} | Уран: {n_uranium}", True, BLACK)
    screen.blit(text2, (10, 35))

    # Получение позиции мыши
    mouse_pos = pygame.mouse.get_pos()

    # Кнопка добавления нейтрона
    neutron_button_hover = add_neutron_button_rect.collidepoint(mouse_pos)
    neutron_button_color = NEUTRON_BUTTON_HOVER_COLOR if neutron_button_hover else NEUTRON_BUTTON_COLOR
    pygame.draw.rect(screen, neutron_button_color, add_neutron_button_rect, border_radius=5)
    pygame.draw.rect(screen, BLACK, add_neutron_button_rect, 2, border_radius=5)
    neutron_text = font.render("+ Нейтрон", True, WHITE)
    screen.blit(neutron_text, (add_neutron_button_rect.centerx - neutron_text.get_width() // 2,
                               add_neutron_button_rect.centery - neutron_text.get_height() // 2))

    # Кнопка паузы
    pause_button_hover = pause_button_rect.collidepoint(mouse_pos)
    pause_button_color = BUTTON_HOVER_COLOR if pause_button_hover else BUTTON_COLOR
    pygame.draw.rect(screen, pause_button_color, pause_button_rect, border_radius=5)
    pygame.draw.rect(screen, BLACK, pause_button_rect, 2, border_radius=5)
    pause_text = font.render("Пауза" if not paused else "Продолжить", True, WHITE)
    screen.blit(pause_text, (pause_button_rect.centerx - pause_text.get_width() // 2,
                             pause_button_rect.centery - pause_text.get_height() // 2))

    # Фон реактора (вода)
    screen.blit(reactor_bg, (0, PANEL_HEIGHT))

    # Сетка реактора
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            pygame.draw.rect(screen, GRAY, (x * CELL_SIZE, y * CELL_SIZE + PANEL_HEIGHT, CELL_SIZE, CELL_SIZE), 1)

    # Технологические каналы с черной обводкой
    for col in uranium_lines:
        x_pos = col * CELL_SIZE

        # Черная обводка
        pygame.draw.line(screen, BLACK, (x_pos, PANEL_HEIGHT), (x_pos, SCREEN_HEIGHT), 6)
        # Белый стержень
        pygame.draw.line(screen, WHITE, (x_pos, PANEL_HEIGHT), (x_pos, SCREEN_HEIGHT), 4)

    # Управляющие стержни с белой обводкой
    for col in rod_columns:
        x_pos = col * CELL_SIZE
        rod_top = PANEL_HEIGHT + rod_depths[col] * CELL_SIZE

        # Белая обводка
        pygame.draw.line(screen, WHITE, (x_pos, PANEL_HEIGHT), (x_pos, rod_top), 6)
        # Черный стержень
        pygame.draw.line(screen, ROD_COLOR, (x_pos, PANEL_HEIGHT), (x_pos, rod_top), 4)

    # Отрисовка частиц
    for p in particles:
        p.draw(screen)

    # Индикатор паузы
    if paused:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        pause_font = pygame.font.SysFont(None, 72)
        pause_text = pause_font.render("ПАУЗА", True, (255, 255, 255))
        screen.blit(pause_text, (SCREEN_WIDTH // 2 - pause_text.get_width() // 2,
                                 SCREEN_HEIGHT // 2 - pause_text.get_height() // 2))


# Основной цикл
running = True
while running:
    clock.tick(FPS)
    keys = pygame.key.get_pressed()

    # Управление стержнями
    speed_multiplier = 3 if keys[pygame.K_LSHIFT] else 1
    for col in rod_columns:
        if keys[pygame.K_UP]:
            rod_depths[col] = max(1, rod_depths[col] - speed_multiplier)
        if keys[pygame.K_DOWN]:
            rod_depths[col] = min(GRID_HEIGHT, rod_depths[col] + speed_multiplier)

    # Обновление частиц
    if not paused:
        # Обработка движения частиц
        for p in particles[:]:
            p.move(particles)

        # Удаление неактивных частиц
        particles = [p for p in particles if p.active]

        # Генерация новых нейтронов
        if len(particles) < MAX_PARTICLES // 2 and random.random() < 0.4:
            particles.append(Particle(
                random.randint(0, GRID_WIDTH - 1),
                random.randint(0, GRID_HEIGHT - 1),
                ParticleType.FAST_NEUTRON
            ))

    # Отрисовка
    draw()
    pygame.display.flip()

    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if pause_button_rect.collidepoint(event.pos):
                paused = not paused
            elif add_neutron_button_rect.collidepoint(event.pos):
                if len(particles) < MAX_PARTICLES:
                    particles.append(Particle(
                        random.randint(0, GRID_WIDTH - 1),
                        random.randint(0, GRID_HEIGHT - 1),
                        ParticleType.FAST_NEUTRON
                    ))

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                paused = not paused
            elif event.key == pygame.K_n:
                if len(particles) < MAX_PARTICLES:
                    particles.append(Particle(
                        random.randint(0, GRID_WIDTH - 1),
                        random.randint(0, GRID_HEIGHT - 1),
                        ParticleType.FAST_NEUTRON
                    ))
            elif event.key == pygame.K_SPACE:
                for _ in range(10):
                    if len(particles) < MAX_PARTICLES:
                        particles.append(Particle(
                            random.randint(0, GRID_WIDTH - 1),
                            random.randint(0, GRID_HEIGHT - 1),
                            ParticleType.FAST_NEUTRON
                        ))
            elif event.key == pygame.K_u:
                for _ in range(5):
                    if len(particles) < MAX_PARTICLES:
                        particles.append(Particle(
                            random.randint(0, GRID_WIDTH - 1),
                            random.randint(0, GRID_HEIGHT - 1),
                            ParticleType.URANIUM
                        ))
            elif event.key == pygame.K_x:
                for _ in range(5):
                    if len(particles) < MAX_PARTICLES:
                        particles.append(Particle(
                            random.randint(0, GRID_WIDTH - 1),
                            random.randint(0, GRID_HEIGHT - 1),
                            ParticleType.XENON
                        ))

pygame.quit()
