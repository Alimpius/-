import pygame
import random
import math
from enum import Enum

#астройки
CELL_SIZE = 24
GRID_WIDTH = 40
GRID_HEIGHT = 21
PANEL_HEIGHT = 60
SCREEN_WIDTH = GRID_WIDTH * CELL_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * CELL_SIZE + PANEL_HEIGHT
FPS = 60
INITIAL_NEUTRONS = 100
MAX_PARTICLES = 1000
WATER_SPAWN_CHANCE = 0.02
MAX_WATER = 150
XENON_SPAWN_CHANCE = 0.01  # Шанс появления ксенона
MAX_XENON = 20  # Максимальное количество ксенона

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (180, 180, 180)
ROD_COLOR = (30, 30, 30)
BG_COLOR = (220, 220, 220)
BLUE = (0, 100, 255)
XENON_COLOR = (100, 0, 100)  # Более заметный цвет ксенона
FAST_NEUTRON_COLOR = (255, 255, 255)
THERMAL_NEUTRON_COLOR = (40, 40, 40)
BUTTON_COLOR = (100, 100, 200)
BUTTON_HOVER_COLOR = (120, 120, 220)
NEUTRON_BUTTON_COLOR = (200, 100, 100)
NEUTRON_BUTTON_HOVER_COLOR = (220, 120, 120)


# Типы частиц
class ParticleType(Enum):
    FAST_NEUTRON = 1
    THERMAL_NEUTRON = 2
    XENON = 3
    WATER = 4


pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Ядерный реактор")
clock = pygame.time.Clock()

#Структура стержней
uranium_lines = [x for x in range(0, GRID_WIDTH, 4)]
rod_columns = [x + 2 for x in uranium_lines if x + 2 < GRID_WIDTH]
rod_depths = {col: GRID_HEIGHT // 2 for col in rod_columns}

#Состояние паузы
paused = False

#Кнопки
pause_button_rect = pygame.Rect(SCREEN_WIDTH - 110, 10, 100, 30)
add_neutron_button_rect = pygame.Rect(SCREEN_WIDTH - 220, 10, 100, 30)  # Новая кнопка


#Класс частиц
class Particle:
    def __init__(self, x, y, particle_type):
        self.x = x * CELL_SIZE + CELL_SIZE // 2
        self.y = y * CELL_SIZE + CELL_SIZE // 2

        # Только нейтроны имеют направление движения
        if particle_type in [ParticleType.FAST_NEUTRON, ParticleType.THERMAL_NEUTRON]:
            angle = random.uniform(0, 2 * math.pi)
            self.vx = math.cos(angle)
            self.vy = math.sin(angle)
        else:
            self.vx = 0
            self.vy = 0

        if particle_type == ParticleType.FAST_NEUTRON:
            self.speed = 4.0
            self.radius = CELL_SIZE // 8
            self.color = FAST_NEUTRON_COLOR
        elif particle_type == ParticleType.THERMAL_NEUTRON:
            self.speed = 1.5
            self.radius = CELL_SIZE // 8
            self.color = THERMAL_NEUTRON_COLOR
        elif particle_type == ParticleType.XENON:
            self.speed = 0.0  # Ксенон статичен
            self.radius = CELL_SIZE // 3  # Ксенон крупнее
            self.color = XENON_COLOR
        elif particle_type == ParticleType.WATER:
            self.speed = 0.0
            self.radius = CELL_SIZE // 6
            self.color = BLUE

        self.type = particle_type
        self.active = True

    def distance_to(self, other):
        return math.hypot(self.x - other.x, self.y - other.y)

    def move(self, particles):
        if not self.active:
            return

        # Движение только для нейтронов
        if self.type in [ParticleType.FAST_NEUTRON, ParticleType.THERMAL_NEUTRON]:
            self.x += self.vx * self.speed
            self.y += self.vy * self.speed

            # Границы реактора
            if self.x - self.radius < 0 or self.x + self.radius > SCREEN_WIDTH:
                self.vx = -self.vx
            if self.y - self.radius < 0 or self.y + self.radius > GRID_HEIGHT * CELL_SIZE:
                self.vy = -self.vy

            # Взаимодействие с водой
            for p in particles:
                if p.type == ParticleType.WATER and p.active and self.distance_to(p) < self.radius + p.radius:
                    if self.type == ParticleType.FAST_NEUTRON:
                        self.type = ParticleType.THERMAL_NEUTRON
                        self.speed = 1.5
                        self.color = THERMAL_NEUTRON_COLOR
                    return

            # Взаимодействие с ураном (деление)
            if self.type == ParticleType.THERMAL_NEUTRON:
                for col in uranium_lines:
                    rod_x = col * CELL_SIZE
                    if abs(self.x - rod_x) < self.radius + 2:
                        if random.random() < 0.5:  # шанс деления
                            self.active = False
                            grid_x = int(self.x / CELL_SIZE)
                            grid_y = int(self.y / CELL_SIZE)
                            particles.append(Particle(grid_x, grid_y, ParticleType.XENON))

                            for _ in range(3):
                                if len(particles) < MAX_PARTICLES:
                                    new_n = Particle(grid_x, grid_y, ParticleType.FAST_NEUTRON)
                                    angle = random.uniform(0, 2 * math.pi)
                                    new_n.vx = math.cos(angle)
                                    new_n.vy = math.sin(angle)
                                    particles.append(new_n)
                        else:
                            # Поглощение без деления
                            self.active = False
                        return

            # Взаимодействие с ксеноном ТОЛЬКО ДЛЯ БЫСТРЫХ НЕЙТРОНОВ
            if self.type == ParticleType.FAST_NEUTRON:
                for p in particles:
                    if p != self and p.type == ParticleType.XENON and p.active and self.distance_to(
                            p) < self.radius + p.radius:
                        if random.random() < 0.8:  #шанс поглощения
                            p.active = False
                            self.active = False
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


#Частицы
particles = [Particle(random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1), ParticleType.FAST_NEUTRON)
             for _ in range(INITIAL_NEUTRONS)]

#начальные частицы воды
initial_water_count = 80
for _ in range(initial_water_count):
    particles.append(Particle(
        random.randint(0, GRID_WIDTH - 1),
        random.randint(0, GRID_HEIGHT - 1),
        ParticleType.WATER
    ))

#начальные частицы ксенона
initial_xenon_count = 5
for _ in range(initial_xenon_count):
    particles.append(Particle(
        random.randint(0, GRID_WIDTH - 1),
        random.randint(0, GRID_HEIGHT - 1),
        ParticleType.XENON
    ))


#Отрисовка
def draw():
    screen.fill(BG_COLOR)

    # Верхняя панель
    pygame.draw.rect(screen, (200, 200, 200), (0, 0, SCREEN_WIDTH, PANEL_HEIGHT))
    font = pygame.font.SysFont(None, 24)

    # Счетчики частиц
    n_fast = len([p for p in particles if p.type == ParticleType.FAST_NEUTRON and p.active])
    n_thermal = len([p for p in particles if p.type == ParticleType.THERMAL_NEUTRON and p.active])
    n_xenon = len([p for p in particles if p.type == ParticleType.XENON and p.active])
    n_water = len([p for p in particles if p.type == ParticleType.WATER and p.active])

    # Отображение статистики
    text = font.render(f"Быстрые: {n_fast} | Тепловые: {n_thermal} | Всего: {n_fast + n_thermal}", True, BLACK)
    screen.blit(text, (10, 10))

    text2 = font.render(f"Ксенон: {n_xenon} | Вода: {n_water}", True, BLACK)
    screen.blit(text2, (10, 35))

    # Получение позиции мыши для определения наведения
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

    # Сетка
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            pygame.draw.rect(screen, GRAY, (x * CELL_SIZE, y * CELL_SIZE + PANEL_HEIGHT, CELL_SIZE, CELL_SIZE), 1)

    # Топливные стержни (уран)
    for col in uranium_lines:
        x_pos = col * CELL_SIZE
        pygame.draw.line(screen, WHITE, (x_pos, PANEL_HEIGHT), (x_pos, SCREEN_HEIGHT), 4)

    # Управляющие стержни
    for col in rod_columns:
        x_pos = col * CELL_SIZE
        rod_top = PANEL_HEIGHT + rod_depths[col] * CELL_SIZE
        pygame.draw.line(screen, ROD_COLOR, (x_pos, PANEL_HEIGHT), (x_pos, rod_top), 4)

    # Частицы
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


#Основной цикл
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

    # Обновление частиц только если не пауза
    if not paused:
        for p in particles[:]:
            p.move(particles)

        # Удаление неактивных частиц
        particles = [p for p in particles if p.active]

        # Случайная генерация новых нейтронов
        if len(particles) < MAX_PARTICLES // 2 and random.random() < 0.05:
            particles.append(Particle(
                random.randint(0, GRID_WIDTH - 1),
                random.randint(0, GRID_HEIGHT - 1),
                ParticleType.FAST_NEUTRON
            ))

        # Рандомная генерация воды
        n_water = len([p for p in particles if p.type == ParticleType.WATER])
        if (n_water < MAX_WATER and
                random.random() < WATER_SPAWN_CHANCE and
                len(particles) < MAX_PARTICLES):
            particles.append(Particle(
                random.randint(0, GRID_WIDTH - 1),
                random.randint(0, GRID_HEIGHT - 1),
                ParticleType.WATER
            ))

        # Рандомная генерация ксенона
        n_xenon = len([p for p in particles if p.type == ParticleType.XENON])
        if (n_xenon < MAX_XENON and
                random.random() < XENON_SPAWN_CHANCE and
                len(particles) < MAX_PARTICLES):
            particles.append(Particle(
                random.randint(0, GRID_WIDTH - 1),
                random.randint(0, GRID_HEIGHT - 1),
                ParticleType.XENON
            ))

    draw()
    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if pause_button_rect.collidepoint(event.pos):
                paused = not paused

            # Проверка клика по кнопке добавления нейтрона
            elif add_neutron_button_rect.collidepoint(event.pos):
                if len(particles) < MAX_PARTICLES:
                    particles.append(Particle(
                        random.randint(0, GRID_WIDTH - 1),
                        random.randint(0, GRID_HEIGHT - 1),
                        ParticleType.FAST_NEUTRON
                    ))

        elif event.type == pygame.KEYDOWN:
            # P для паузы
            if event.key == pygame.K_p:
                paused = not paused

            # N для добавления нейтрона
            elif event.key == pygame.K_n:
                if len(particles) < MAX_PARTICLES:
                    particles.append(Particle(
                        random.randint(0, GRID_WIDTH - 1),
                        random.randint(0, GRID_HEIGHT - 1),
                        ParticleType.FAST_NEUTRON
                    ))

            elif event.key == pygame.K_SPACE:
                # Добавление группы нейтронов
                for _ in range(10):
                    if len(particles) < MAX_PARTICLES:
                        particles.append(Particle(
                            random.randint(0, GRID_WIDTH - 1),
                            random.randint(0, GRID_HEIGHT - 1),
                            ParticleType.FAST_NEUTRON
                        ))
            elif event.key == pygame.K_w:
                # Ручное добавление воды
                for _ in range(5):
                    if len(particles) < MAX_PARTICLES:
                        particles.append(Particle(
                            random.randint(0, GRID_WIDTH - 1),
                            random.randint(0, GRID_HEIGHT - 1),
                            ParticleType.WATER
                        ))
            elif event.key == pygame.K_x:
                # Ручное добавление ксенона
                for _ in range(5):
                    if len(particles) < MAX_PARTICLES:
                        particles.append(Particle(
                            random.randint(0, GRID_WIDTH - 1),
                            random.randint(0, GRID_HEIGHT - 1),
                            ParticleType.XENON
                        ))

pygame.quit()