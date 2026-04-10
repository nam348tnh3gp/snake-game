import pygame
import random
import sys
import os
import math
from collections import deque

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 800, 600
CELL_SIZE = 20
GRID_WIDTH = WIDTH // CELL_SIZE
GRID_HEIGHT = HEIGHT // CELL_SIZE

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
DARK_GREEN = (0, 150, 0)
GOLD = (255, 215, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
LIGHT_GREEN = (0, 200, 0)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
PINK = (255, 105, 180)
BROWN = (139, 69, 19)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake game")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
large_font = pygame.font.Font(None, 72)
small_font = pygame.font.Font(None, 24)

HIGH_SCORE_FILE = "snake_highscore.txt"
FRENZY_DURATION = 300
TRAIL_LENGTH = 8
OBSTACLE_SPAWN_SCORE = 15
BASE_SPEED = 10
MAX_SPEED = 28

try:
    eat_sound = pygame.mixer.Sound("eat.wav")
    game_over_sound = pygame.mixer.Sound("gameover.wav")
    frenzy_sound = pygame.mixer.Sound("frenzy.wav")
    obstacle_sound = pygame.mixer.Sound("obstacle.wav")
except:
    eat_sound = game_over_sound = frenzy_sound = obstacle_sound = None
    print("Audio files not found - playing without sound")

class Particle:
    def __init__(self, x, y, color, text=None):
        self.x = x
        self.y = y
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-6, -2)
        self.color = color
        self.life = 30
        self.size = random.randint(2, 6)
        self.text = text
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3
        self.life -= 1
        self.size = max(1, self.size - 0.15)
    
    def draw(self, screen, offset_x=0, offset_y=0):
        if self.life > 0:
            if self.text:
                alpha = min(255, self.life * 8)
                text_surf = font.render(self.text, True, self.color)
                text_surf.set_alpha(alpha)
                screen.blit(text_surf, (int(self.x + offset_x), int(self.y + offset_y)))
            else:
                pygame.draw.circle(screen, self.color, (int(self.x + offset_x), int(self.y + offset_y)), int(self.size))

class Obstacle:
    def __init__(self, pos):
        self.pos = pos
        self.spawn_time = pygame.time.get_ticks()
        self.blink_duration = 500
        self.is_active = False
    
    def update(self):
        if not self.is_active and pygame.time.get_ticks() - self.spawn_time > self.blink_duration:
            self.is_active = True
    
    def draw(self, screen, offset_x=0, offset_y=0):
        x, y = self.pos[0] * CELL_SIZE + offset_x, self.pos[1] * CELL_SIZE + offset_y
        if not self.is_active:
            blink = abs(math.sin(pygame.time.get_ticks() * 0.01)) > 0.5
            color = RED if blink else BROWN
        else:
            color = BROWN
        pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE), border_radius=4)
        pygame.draw.rect(screen, (100, 50, 0), (x + 2, y + 2, CELL_SIZE - 4, CELL_SIZE - 4), border_radius=2)

def load_high_score():
    if os.path.exists(HIGH_SCORE_FILE):
        try:
            with open(HIGH_SCORE_FILE, "r") as f:
                return int(f.read())
        except:
            return 0
    return 0

def save_high_score(score):
    try:
        with open(HIGH_SCORE_FILE, "w") as f:
            f.write(str(score))
    except:
        pass

# Hàm vẽ lưới không còn được sử dụng nữa, có thể giữ lại hoặc xóa.
# def draw_grid():
#     for x in range(0, WIDTH, CELL_SIZE):
#         pygame.draw.line(screen, GRAY, (x, 0), (x, HEIGHT), 1)
#     for y in range(0, HEIGHT, CELL_SIZE):
#         pygame.draw.line(screen, GRAY, (0, y), (WIDTH, y), 1)

def draw_snake(snake, offset_x=0, offset_y=0, frenzy=False, trail_history=None):
    if trail_history and frenzy:
        for i, old_snake in enumerate(trail_history):
            alpha = max(20, int(100 - i * (100 / TRAIL_LENGTH)))
            for segment in old_snake:
                x, y = segment[0] * CELL_SIZE + offset_x, segment[1] * CELL_SIZE + offset_y
                trail_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(trail_surf, (0, 255, 0, alpha), (0, 0, CELL_SIZE, CELL_SIZE), border_radius=6)
                screen.blit(trail_surf, (x, y))
    
    for i, segment in enumerate(snake):
        x, y = segment[0] * CELL_SIZE + offset_x, segment[1] * CELL_SIZE + offset_y
        
        if frenzy:
            time_ms = pygame.time.get_ticks()
            color_val = (time_ms // 50 + i * 10) % 360
            body_color = pygame.Color(0)
            body_color.hsla = (color_val, 100, 50, 100)
            head_color = pygame.Color(0)
            head_color.hsla = ((color_val + 60) % 360, 100, 60, 100)
        else:
            body_color = GREEN
            head_color = DARK_GREEN
        
        if i == 0:
            pygame.draw.rect(screen, head_color, (x, y, CELL_SIZE, CELL_SIZE), border_radius=8)
            pygame.draw.rect(screen, BLACK, (x, y, CELL_SIZE, CELL_SIZE), 2, border_radius=8)
            eye_size = 3
            eye_offset = 5
            pygame.draw.circle(screen, WHITE, (x + eye_offset, y + eye_offset), eye_size)
            pygame.draw.circle(screen, WHITE, (x + CELL_SIZE - eye_offset, y + eye_offset), eye_size)
            pygame.draw.circle(screen, BLACK, (x + eye_offset, y + eye_offset), 1)
            pygame.draw.circle(screen, BLACK, (x + CELL_SIZE - eye_offset, y + eye_offset), 1)
            if frenzy:
                pygame.draw.circle(screen, PINK, (x + eye_offset, y + eye_offset), eye_size + 2, 1)
                pygame.draw.circle(screen, PINK, (x + CELL_SIZE - eye_offset, y + eye_offset), eye_size + 2, 1)
        else:
            pygame.draw.rect(screen, body_color, (x, y, CELL_SIZE, CELL_SIZE), border_radius=6)
            inner_rect = (x + 2, y + 2, CELL_SIZE - 4, CELL_SIZE - 4)
            pygame.draw.rect(screen, (min(255, body_color[0] + 40), min(255, body_color[1] + 40), min(255, body_color[2] + 40)), inner_rect, border_radius=3)
            pygame.draw.rect(screen, BLACK, (x, y, CELL_SIZE, CELL_SIZE), 1, border_radius=6)

def draw_food(food, food_type, offset_x=0, offset_y=0):
    x, y = food[0] * CELL_SIZE + offset_x, food[1] * CELL_SIZE + offset_y
    center = (x + CELL_SIZE // 2, y + CELL_SIZE // 2)
    
    if food_type == "golden":
        pygame.draw.circle(screen, GOLD, center, CELL_SIZE // 2 - 2)
        pygame.draw.circle(screen, YELLOW, center, CELL_SIZE // 3)
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            tx = center[0] + math.cos(rad) * (CELL_SIZE // 3)
            ty = center[1] + math.sin(rad) * (CELL_SIZE // 3)
            pygame.draw.circle(screen, ORANGE, (int(tx), int(ty)), 2)
    elif food_type == "blue":
        pygame.draw.circle(screen, BLUE, center, CELL_SIZE // 2 - 2)
        pygame.draw.circle(screen, (100, 100, 255), center, CELL_SIZE // 3)
    elif food_type == "purple":
        pygame.draw.circle(screen, PURPLE, center, CELL_SIZE // 2 - 2)
        pygame.draw.circle(screen, (200, 100, 200), center, CELL_SIZE // 3)
    else:
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 5
        pygame.draw.circle(screen, RED, center, CELL_SIZE // 2 - 2 + int(pulse * 0.2))
        pygame.draw.circle(screen, YELLOW, center, CELL_SIZE // 4)

def draw_score(score, high_score, frenzy_end_time):
    score_text = font.render(f"Score: {score}", True, WHITE)
    high_score_text = font.render(f"High Score: {high_score}", True, YELLOW)
    screen.blit(score_text, (10, 10))
    screen.blit(high_score_text, (10, 50))
    
    if frenzy_end_time > pygame.time.get_ticks():
        remaining_ms = frenzy_end_time - pygame.time.get_ticks()
        remaining_sec = remaining_ms // 1000 + 1
        frenzy_text = font.render(f"FRENZY MODE: {remaining_sec}s", True, PINK)
        screen.blit(frenzy_text, (WIDTH // 2 - frenzy_text.get_width() // 2, 20))

def draw_game_over(score):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    
    game_over_text = large_font.render("GAME OVER", True, RED)
    score_text = font.render(f"Your Score: {score}", True, WHITE)
    restart_text = font.render("Press SPACE to play again or ESC to quit", True, WHITE)
    
    screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 100))
    screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 - 30))
    screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 30))

def draw_pause():
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(150)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    
    pause_text = large_font.render("PAUSED", True, YELLOW)
    continue_text = font.render("Press P to continue", True, WHITE)
    
    screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - 50))
    screen.blit(continue_text, (WIDTH // 2 - continue_text.get_width() // 2, HEIGHT // 2 + 20))

def draw_welcome():
    screen.fill(BLACK)
    title_text = large_font.render("SNAKE GAME", True, GREEN)
    control_text1 = font.render("Use ARROW KEYS or WASD to move", True, WHITE)
    control_text2 = font.render("Press P to pause | Press W for Wall Mode", True, WHITE)
    control_text3 = font.render("Eat PURPLE for FRENZY | Avoid BROWN obstacles!", True, PINK)
    control_text4 = font.render("Press SPACE to start", True, WHITE)
    
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 2 - 100))
    screen.blit(control_text1, (WIDTH // 2 - control_text1.get_width() // 2, HEIGHT // 2 - 20))
    screen.blit(control_text2, (WIDTH // 2 - control_text2.get_width() // 2, HEIGHT // 2 + 10))
    screen.blit(control_text3, (WIDTH // 2 - control_text3.get_width() // 2, HEIGHT // 2 + 40))
    screen.blit(control_text4, (WIDTH // 2 - control_text4.get_width() // 2, HEIGHT // 2 + 80))
    
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

def get_random_empty_position(snake, obstacles, retry_count=0):
    if len(snake) >= GRID_WIDTH * GRID_HEIGHT - len(obstacles):
        return None
    
    if retry_count < 50:
        x = random.randint(0, GRID_WIDTH - 1)
        y = random.randint(0, GRID_HEIGHT - 1)
        pos = [x, y]
        if pos in snake or pos in [obs.pos for obs in obstacles]:
            return get_random_empty_position(snake, obstacles, retry_count + 1)
        return pos
    
    all_cells = [[x, y] for x in range(GRID_WIDTH) for y in range(GRID_HEIGHT)]
    occupied = set(tuple(pos) for pos in snake) | set(tuple(obs.pos) for obs in obstacles)
    empty_cells = [cell for cell in all_cells if tuple(cell) not in occupied]
    if not empty_cells:
        return None
    return random.choice(empty_cells)

def get_food_type(score):
    rand = random.random()
    if score >= 20 and rand < 0.08:
        return "purple"
    elif score >= 12 and rand < 0.12:
        return "blue"
    elif score >= 6 and rand < 0.18:
        return "golden"
    return "normal"

def apply_food_effect(food_type, base_speed, score, frenzy_end_time):
    if food_type == "golden":
        return min(MAX_SPEED, base_speed + 2), score + 5, frenzy_end_time
    elif food_type == "blue":
        return max(BASE_SPEED, base_speed - 2), score + 2, frenzy_end_time
    elif food_type == "purple":
        if frenzy_sound:
            frenzy_sound.play()
        return min(MAX_SPEED, base_speed + 3), score + 10, pygame.time.get_ticks() + FRENZY_DURATION
    return base_speed, score + 1, frenzy_end_time

def main():
    high_score = load_high_score()
    
    while True:
        draw_welcome()
        
        snake = deque([[GRID_WIDTH // 2, GRID_HEIGHT // 2]])
        direction = [1, 0]
        direction_queue = []
        obstacles = []
        food = get_random_empty_position(snake, obstacles)
        food_type = "normal"
        score = 0
        base_speed = BASE_SPEED
        paused = False
        running = True
        particles = []
        wall_mode = False
        shake_amount = 0
        frenzy_end_time = 0
        trail_history = deque(maxlen=TRAIL_LENGTH)
        last_obstacle_score = 0
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    
                    if event.key == pygame.K_p:
                        paused = not paused
                    
                    if event.key == pygame.K_w:
                        wall_mode = not wall_mode
                    
                    if not paused:
                        if event.key in (pygame.K_UP, pygame.K_w):
                            direction_queue.append([0, -1])
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            direction_queue.append([0, 1])
                        elif event.key in (pygame.K_LEFT, pygame.K_a):
                            direction_queue.append([-1, 0])
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            direction_queue.append([1, 0])
            
            if paused:
                screen.fill(BLACK)
                # draw_grid()  # <-- ĐÃ LOẠI BỎ
                for obs in obstacles:
                    obs.draw(screen)
                draw_snake(snake, 0, 0, pygame.time.get_ticks() < frenzy_end_time)
                draw_food(food, food_type)
                draw_score(score, high_score, frenzy_end_time)
                draw_pause()
                pygame.display.flip()
                clock.tick(30)
                continue
            
            for obs in obstacles:
                obs.update()
            
            trail_history.append(list(snake))
            
            if direction_queue:
                potential_dir = direction_queue.pop(0)
                if potential_dir[0] * -1 != direction[0] or potential_dir[1] * -1 != direction[1]:
                    direction = potential_dir
            
            new_head = [snake[0][0] + direction[0], snake[0][1] + direction[1]]
            is_frenzy = pygame.time.get_ticks() < frenzy_end_time
            current_speed = base_speed + (3 if is_frenzy else 0)
            
            if wall_mode:
                new_head[0] %= GRID_WIDTH
                new_head[1] %= GRID_HEIGHT
                if new_head[0] < 0: new_head[0] = GRID_WIDTH - 1
                if new_head[1] < 0: new_head[1] = GRID_HEIGHT - 1
            else:
                if new_head[0] < 0 or new_head[0] >= GRID_WIDTH or new_head[1] < 0 or new_head[1] >= GRID_HEIGHT:
                    if game_over_sound:
                        game_over_sound.play()
                    running = False
                    break
            
            active_obstacles = [obs for obs in obstacles if obs.is_active]
            if not is_frenzy and (new_head in snake or new_head in [obs.pos for obs in active_obstacles]):
                if game_over_sound:
                    game_over_sound.play()
                running = False
                break
            
            snake.appendleft(new_head)
            
            if new_head == food:
                if eat_sound:
                    eat_sound.play()
                
                center_x = new_head[0] * CELL_SIZE + CELL_SIZE // 2
                center_y = new_head[1] * CELL_SIZE + CELL_SIZE // 2
                
                points = 0
                if food_type == "golden":
                    for _ in range(25):
                        particles.append(Particle(center_x, center_y, GOLD))
                    shake_amount = 6
                    points = 5
                elif food_type == "blue":
                    for _ in range(15):
                        particles.append(Particle(center_x, center_y, BLUE))
                    shake_amount = 3
                    points = 2
                elif food_type == "purple":
                    for _ in range(40):
                        particles.append(Particle(center_x, center_y, PURPLE))
                    shake_amount = 12
                    points = 10
                else:
                    for _ in range(12):
                        particles.append(Particle(center_x, center_y, YELLOW))
                    shake_amount = 2
                    points = 1
                
                particles.append(Particle(center_x, center_y - 10, YELLOW, f"+{points}"))
                
                base_speed, score, frenzy_end_time = apply_food_effect(
                    food_type, base_speed, score, frenzy_end_time
                )
                
                if score >= OBSTACLE_SPAWN_SCORE and score // OBSTACLE_SPAWN_SCORE > last_obstacle_score:
                    last_obstacle_score = score // OBSTACLE_SPAWN_SCORE
                    pos = get_random_empty_position(snake, obstacles)
                    if pos:
                        obstacles.append(Obstacle(pos))
                        if obstacle_sound:
                            obstacle_sound.play()
                
                food = get_random_empty_position(snake, obstacles)
                if food is None:
                    running = False
                    break
                food_type = get_food_type(score)
            else:
                snake.pop()
            
            particles = [p for p in particles if p.life > 0]
            for p in particles:
                p.update()
            
            if shake_amount > 0:
                shake_amount -= 0.5
            
            offset_x = random.randint(-int(shake_amount), int(shake_amount)) if shake_amount > 0 else 0
            offset_y = random.randint(-int(shake_amount), int(shake_amount)) if shake_amount > 0 else 0
            
            wall_mode_text = small_font.render(f"Wall Mode: {'ON' if wall_mode else 'OFF'} (Press W)", True, GRAY)
            food_info = small_font.render(f"Next Food: {food_type.upper()}", True, YELLOW)
            obstacle_info = small_font.render(f"Obstacles: {len(obstacles)}", True, BROWN)
            speed_info = small_font.render(f"Speed: {current_speed}", True, CYAN)
            
            screen.fill(BLACK)
            # draw_grid()  # <-- ĐÃ LOẠI BỎ
            for obs in obstacles:
                obs.draw(screen, offset_x, offset_y)
            draw_snake(snake, offset_x, offset_y, is_frenzy, list(trail_history) if is_frenzy else None)
            draw_food(food, food_type, offset_x, offset_y)
            draw_score(score, high_score, frenzy_end_time)
            for p in particles:
                p.draw(screen, offset_x, offset_y)
            screen.blit(wall_mode_text, (10, HEIGHT - 30))
            screen.blit(food_info, (WIDTH - 180, HEIGHT - 30))
            screen.blit(obstacle_info, (WIDTH - 150, HEIGHT - 60))
            screen.blit(speed_info, (10, HEIGHT - 60))
            pygame.display.flip()
            clock.tick(current_speed)
        
        if score > high_score:
            high_score = score
            save_high_score(high_score)
        
        game_over = True
        while game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        game_over = False
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
            
            screen.fill(BLACK)
            # draw_grid()  # <-- ĐÃ LOẠI BỎ
            for obs in obstacles:
                obs.draw(screen)
            draw_snake(snake, 0, 0, False)
            if food:
                draw_food(food, food_type)
            draw_game_over(score)
            pygame.display.flip()
            clock.tick(30)

if __name__ == "__main__":
    main()
