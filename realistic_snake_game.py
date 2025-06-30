import pygame
import random
import math
import sys
from enum import Enum
import time

# Initialize Pygame
pygame.init()

# Optimized constants for Raspberry Pi Zero 2W
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
GRID_SIZE = 25  # Larger grid for better performance
GRID_WIDTH = WINDOW_WIDTH // GRID_SIZE
GRID_HEIGHT = WINDOW_HEIGHT // GRID_SIZE
FPS = 30  # Reduced FPS for Pi Zero 2W

# Simplified colors for better performance
COLORS = {
    'BLACK': (0, 0, 0),
    'WHITE': (255, 255, 255),
    'DARK_GREEN': (34, 100, 34),
    'SNAKE_HEAD': (85, 107, 47),
    'SNAKE_BODY': (107, 142, 35),
    'APPLE_RED': (220, 20, 60),
    'APPLE_HIGHLIGHT': (255, 100, 100),
    'OBSTACLE': (139, 69, 19),
    'GRID_LINE': (20, 60, 20),
    'UI_GREEN': (50, 205, 50)
}

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class Particle:
    """Lightweight particle for Pi Zero 2W"""
    def __init__(self, x, y, velocity, lifetime):
        self.x = x
        self.y = y
        self.vx, self.vy = velocity
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        
    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.lifetime -= dt
        
    def draw(self, screen):
        if self.lifetime > 0:
            alpha_factor = self.lifetime / self.max_lifetime
            size = max(1, int(2 * alpha_factor))
            pygame.draw.circle(screen, COLORS['APPLE_RED'], 
                             (int(self.x), int(self.y)), size)

class ParticleSystem:
    """Optimized particle system"""
    def __init__(self):
        self.particles = []
        self.max_particles = 20  # Limit particles for performance
    
    def add_explosion(self, x, y, count=8):  # Reduced particle count
        if len(self.particles) > self.max_particles:
            return
            
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30, 80)
            velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
            lifetime = random.uniform(0.3, 0.8)
            self.particles.append(Particle(x, y, velocity, lifetime))
    
    def update(self, dt):
        self.particles = [p for p in self.particles if p.lifetime > 0]
        for particle in self.particles:
            particle.update(dt)
    
    def draw(self, screen):
        for particle in self.particles:
            particle.draw(screen)

class Snake:
    def __init__(self, start_x, start_y):
        self.segments = [(start_x, start_y)]
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.growing = False
        self.move_timer = 0
        self.move_delay = 0.2  # Slower for Pi Zero 2W
        
    def update(self, dt):
        self.move_timer += dt
        
        if self.move_timer >= self.move_delay:
            self.move_timer = 0
            self.move()
    
    def set_direction(self, direction):
        if len(self.segments) > 1:
            opposite = {
                Direction.UP: Direction.DOWN,
                Direction.DOWN: Direction.UP,
                Direction.LEFT: Direction.RIGHT,
                Direction.RIGHT: Direction.LEFT
            }
            if direction != opposite[self.direction]:
                self.next_direction = direction
        else:
            self.next_direction = direction
    
    def move(self):
        self.direction = self.next_direction
        
        # Get head position
        head_x, head_y = self.segments[0]
        dx, dy = self.direction.value
        new_head = (head_x + dx, head_y + dy)
        
        # Add new head
        self.segments.insert(0, new_head)
        
        # Remove tail unless growing
        if not self.growing:
            self.segments.pop()
        else:
            self.growing = False
    
    def grow(self):
        self.growing = True
    
    def get_head_position(self):
        return self.segments[0]
    
    def check_collision(self, x, y):
        return (x, y) in self.segments
    
    def check_wall_collision(self):
        head_x, head_y = self.get_head_position()
        return (head_x < 0 or head_x >= GRID_WIDTH or 
                head_y < 0 or head_y >= GRID_HEIGHT)
    
    def check_self_collision(self):
        head = self.get_head_position()
        return head in self.segments[1:]
    
    def draw(self, screen):
        for i, (x, y) in enumerate(self.segments):
            pixel_x = x * GRID_SIZE
            pixel_y = y * GRID_SIZE
            rect = pygame.Rect(pixel_x, pixel_y, GRID_SIZE, GRID_SIZE)
            
            if i == 0:  # Head
                # Draw head with simple details
                pygame.draw.rect(screen, COLORS['SNAKE_HEAD'], rect)
                pygame.draw.rect(screen, COLORS['BLACK'], rect, 2)
                
                # Simple eyes
                eye_size = 3
                if self.direction == Direction.RIGHT:
                    eye1 = (pixel_x + GRID_SIZE - 8, pixel_y + 6)
                    eye2 = (pixel_x + GRID_SIZE - 8, pixel_y + GRID_SIZE - 9)
                elif self.direction == Direction.LEFT:
                    eye1 = (pixel_x + 5, pixel_y + 6)
                    eye2 = (pixel_x + 5, pixel_y + GRID_SIZE - 9)
                elif self.direction == Direction.UP:
                    eye1 = (pixel_x + 6, pixel_y + 5)
                    eye2 = (pixel_x + GRID_SIZE - 9, pixel_y + 5)
                else:  # DOWN
                    eye1 = (pixel_x + 6, pixel_y + GRID_SIZE - 8)
                    eye2 = (pixel_x + GRID_SIZE - 9, pixel_y + GRID_SIZE - 8)
                
                pygame.draw.circle(screen, COLORS['WHITE'], eye1, eye_size)
                pygame.draw.circle(screen, COLORS['WHITE'], eye2, eye_size)
                pygame.draw.circle(screen, COLORS['BLACK'], eye1, 1)
                pygame.draw.circle(screen, COLORS['BLACK'], eye2, 1)
                
            else:  # Body
                pygame.draw.rect(screen, COLORS['SNAKE_BODY'], rect)
                pygame.draw.rect(screen, COLORS['BLACK'], rect, 1)

class Apple:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.pulse_time = 0
        
    def update(self, dt):
        self.pulse_time += dt * 2  # Slower pulse for performance
    
    def draw(self, screen):
        # Simple pulsing apple
        pulse = 1 + 0.1 * math.sin(self.pulse_time)
        size = int(GRID_SIZE * 0.7 * pulse)
        
        apple_x = self.x * GRID_SIZE + GRID_SIZE // 2
        apple_y = self.y * GRID_SIZE + GRID_SIZE // 2
        
        # Simple apple with highlight
        pygame.draw.circle(screen, COLORS['APPLE_RED'], (apple_x, apple_y), size//2)
        highlight_x = apple_x - size // 6
        highlight_y = apple_y - size // 6
        pygame.draw.circle(screen, COLORS['APPLE_HIGHLIGHT'], 
                         (highlight_x, highlight_y), max(1, size//6))

class Obstacle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
    def draw(self, screen):
        # Simple obstacle
        obstacle_rect = pygame.Rect(self.x * GRID_SIZE, self.y * GRID_SIZE, 
                                  GRID_SIZE, GRID_SIZE)
        pygame.draw.rect(screen, COLORS['OBSTACLE'], obstacle_rect)
        pygame.draw.rect(screen, COLORS['BLACK'], obstacle_rect, 2)

class Game:
    def __init__(self):
        # Try fullscreen for Pi, fallback to windowed
        try:
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), 
                                                pygame.FULLSCREEN)
        except:
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
            
        pygame.display.set_caption("Pi Snake Game")
        self.clock = pygame.time.Clock()
        
        # Use default font for better Pi compatibility
        self.font = pygame.font.Font(None, 28)
        self.big_font = pygame.font.Font(None, 48)
        
        self.reset_game()
        self.particle_system = ParticleSystem()
        
        # Performance tracking
        self.frame_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0
        
    def reset_game(self):
        self.snake = Snake(GRID_WIDTH // 2, GRID_HEIGHT // 2)
        self.apple = None
        self.obstacles = []
        self.score = 0
        self.apples_eaten = 0
        self.game_over = False
        self.paused = False
        self.spawn_apple()
        
    def spawn_apple(self):
        attempts = 0
        while attempts < 100:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            
            if not self.snake.check_collision(x, y) and not self.is_obstacle(x, y):
                self.apple = Apple(x, y)
                break
            attempts += 1
    
    def spawn_obstacles(self):
        # Fewer obstacles for Pi performance
        obstacle_count = min(6, (self.apples_eaten // 5) + 1)
        
        for _ in range(obstacle_count):
            attempts = 0
            while attempts < 30:
                x = random.randint(0, GRID_WIDTH - 1)
                y = random.randint(0, GRID_HEIGHT - 1)
                
                if (not self.snake.check_collision(x, y) and 
                    not self.is_obstacle(x, y) and 
                    (self.apple is None or (x != self.apple.x or y != self.apple.y))):
                    self.obstacles.append(Obstacle(x, y))
                    break
                attempts += 1
    
    def is_obstacle(self, x, y):
        return any(obs.x == x and obs.y == y for obs in self.obstacles)
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    return False
                elif event.key == pygame.K_r and self.game_over:
                    self.reset_game()
                elif event.key == pygame.K_SPACE or event.key == pygame.K_p:
                    self.paused = not self.paused
                elif not self.game_over and not self.paused:
                    if event.key in [pygame.K_UP, pygame.K_w]:
                        self.snake.set_direction(Direction.UP)
                    elif event.key in [pygame.K_DOWN, pygame.K_s]:
                        self.snake.set_direction(Direction.DOWN)
                    elif event.key in [pygame.K_LEFT, pygame.K_a]:
                        self.snake.set_direction(Direction.LEFT)
                    elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                        self.snake.set_direction(Direction.RIGHT)
        
        return True
    
    def update(self, dt):
        if self.game_over or self.paused:
            return
        
        # Update FPS counter
        self.frame_count += 1
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            self.current_fps = self.frame_count
            self.frame_count = 0
            self.last_fps_time = current_time
        
        self.snake.update(dt)
        
        if self.apple:
            self.apple.update(dt)
        
        self.particle_system.update(dt)
        
        # Check apple collision
        head_pos = self.snake.get_head_position()
        if self.apple and head_pos == (self.apple.x, self.apple.y):
            self.snake.grow()
            self.score += 10
            self.apples_eaten += 1
            
            # Add particles
            apple_pixel_x = self.apple.x * GRID_SIZE + GRID_SIZE // 2
            apple_pixel_y = self.apple.y * GRID_SIZE + GRID_SIZE // 2
            self.particle_system.add_explosion(apple_pixel_x, apple_pixel_y, 6)
            
            self.spawn_apple()
            
            # Add obstacles every 5 apples
            if self.apples_eaten % 5 == 0:
                self.spawn_obstacles()
                # Speed up slightly
                self.snake.move_delay = max(0.1, self.snake.move_delay - 0.02)
        
        # Check collisions
        head_x, head_y = head_pos
        
        if (self.snake.check_wall_collision() or 
            self.snake.check_self_collision() or 
            self.is_obstacle(head_x, head_y)):
            self.game_over = True
            # Add explosion
            pixel_x = head_x * GRID_SIZE + GRID_SIZE // 2
            pixel_y = head_y * GRID_SIZE + GRID_SIZE // 2
            self.particle_system.add_explosion(pixel_x, pixel_y, 10)
    
    def draw(self):
        # Simple background
        self.screen.fill(COLORS['DARK_GREEN'])
        
        # Optional grid (can be disabled for better performance)
        if self.current_fps > 20:  # Only draw grid if FPS is good
            for x in range(0, WINDOW_WIDTH, GRID_SIZE):
                pygame.draw.line(self.screen, COLORS['GRID_LINE'], 
                               (x, 0), (x, WINDOW_HEIGHT), 1)
            for y in range(0, WINDOW_HEIGHT, GRID_SIZE):
                pygame.draw.line(self.screen, COLORS['GRID_LINE'], 
                               (0, y), (WINDOW_WIDTH, y), 1)
        
        # Draw game objects
        for obstacle in self.obstacles:
            obstacle.draw(self.screen)
        
        if self.apple:
            self.apple.draw(self.screen)
        
        self.snake.draw(self.screen)
        self.particle_system.draw(self.screen)
        
        # UI
        self.draw_ui()
    
    def draw_ui(self):
        # Compact UI for Pi
        ui_texts = [
            f"Score: {self.score}",
            f"Apples: {self.apples_eaten}",
            f"FPS: {self.current_fps}"
        ]
        
        for i, text in enumerate(ui_texts):
            rendered = self.font.render(text, True, COLORS['UI_GREEN'])
            self.screen.blit(rendered, (10, 10 + i * 25))
        
        # Controls hint
        controls_text = self.font.render("WASD/Arrows:Move P:Pause Q:Quit", 
                                       True, COLORS['WHITE'])
        self.screen.blit(controls_text, (10, WINDOW_HEIGHT - 30))
        
        if self.paused:
            pause_text = self.big_font.render("PAUSED", True, COLORS['WHITE'])
            text_rect = pause_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
            self.screen.blit(pause_text, text_rect)
        
        if self.game_over:
            game_over_text = self.big_font.render("GAME OVER", True, COLORS['APPLE_RED'])
            restart_text = self.font.render("Press R to restart", True, COLORS['WHITE'])
            
            go_rect = game_over_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 30))
            r_rect = restart_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 10))
            
            self.screen.blit(game_over_text, go_rect)
            self.screen.blit(restart_text, r_rect)
    
    def run(self):
        running = True
        last_time = time.time()
        
        print("Snake Game for Raspberry Pi Zero 2W")
        print("Controls: WASD/Arrow keys to move, P to pause, Q to quit")
        
        while running:
            current_time = time.time()
            dt = min(current_time - last_time, 0.05)  # Cap delta time
            last_time = current_time
            
            running = self.handle_events()
            self.update(dt)
            self.draw()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    try:
        game = Game()
        game.run()
    except Exception as e:
        print(f"Error running game: {e}")
        pygame.quit()
        sys.exit()