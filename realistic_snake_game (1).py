import pygame
import random
import math
import sys
from enum import Enum
from typing import List, Tuple
import time

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
GRID_SIZE = 20
GRID_WIDTH = WINDOW_WIDTH // GRID_SIZE
GRID_HEIGHT = WINDOW_HEIGHT // GRID_SIZE

# Colors with realistic tones
COLORS = {
    'BLACK': (0, 0, 0),
    'WHITE': (255, 255, 255),
    'DARK_GREEN': (34, 139, 34),
    'FOREST_GREEN': (40, 100, 40),
    'SNAKE_HEAD': (85, 107, 47),
    'SNAKE_BODY': (107, 142, 35),
    'SNAKE_BELLY': (154, 205, 50),
    'APPLE_RED': (220, 20, 60),
    'APPLE_HIGHLIGHT': (255, 69, 0),
    'OBSTACLE_BROWN': (139, 69, 19),
    'OBSTACLE_DARK': (101, 67, 33),
    'GRID_LINE': (20, 60, 20),
    'UI_GREEN': (50, 205, 50),
    'SHADOW': (0, 0, 0, 100)
}

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class Particle:
    def __init__(self, x, y, color, velocity, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.velocity = velocity
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        
    def update(self, dt):
        self.x += self.velocity[0] * dt
        self.y += self.velocity[1] * dt
        self.lifetime -= dt
        
    def draw(self, screen):
        if self.lifetime > 0:
            alpha = int(255 * (self.lifetime / self.max_lifetime))
            color = (*self.color[:3], alpha)
            size = max(1, int(3 * (self.lifetime / self.max_lifetime)))
            pygame.draw.circle(screen, color[:3], (int(self.x), int(self.y)), size)

class ParticleSystem:
    def __init__(self):
        self.particles = []
    
    def add_explosion(self, x, y, color, count=15):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
            lifetime = random.uniform(0.5, 1.5)
            self.particles.append(Particle(x, y, color, velocity, lifetime))
    
    def update(self, dt):
        self.particles = [p for p in self.particles if p.lifetime > 0]
        for particle in self.particles:
            particle.update(dt)
    
    def draw(self, screen):
        for particle in self.particles:
            particle.draw(screen)

class SnakeSegment:
    def __init__(self, x, y, is_head=False):
        self.x = x
        self.y = y
        self.is_head = is_head
        self.prev_x = x
        self.prev_y = y
        self.smooth_x = x * GRID_SIZE
        self.smooth_y = y * GRID_SIZE
        self.rotation = 0
        
    def update_smooth_position(self, interpolation_factor):
        target_x = self.x * GRID_SIZE
        target_y = self.y * GRID_SIZE
        self.smooth_x += (target_x - self.smooth_x) * interpolation_factor
        self.smooth_y += (target_y - self.smooth_y) * interpolation_factor

class Apple:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.pulse_time = 0
        self.sparkle_particles = []
        
    def update(self, dt):
        self.pulse_time += dt * 3
        # Add sparkle effects
        if random.random() < 0.1:
            offset_x = random.randint(-10, 10)
            offset_y = random.randint(-10, 10)
            self.sparkle_particles.append({
                'x': self.x * GRID_SIZE + GRID_SIZE//2 + offset_x,
                'y': self.y * GRID_SIZE + GRID_SIZE//2 + offset_y,
                'life': 1.0
            })
        
        # Update sparkles
        for sparkle in self.sparkle_particles[:]:
            sparkle['life'] -= dt * 2
            if sparkle['life'] <= 0:
                self.sparkle_particles.remove(sparkle)
    
    def draw(self, screen):
        # Calculate pulsing effect
        pulse = 1 + 0.1 * math.sin(self.pulse_time)
        size = int(GRID_SIZE * 0.8 * pulse)
        
        # Apple position
        apple_x = self.x * GRID_SIZE + GRID_SIZE // 2
        apple_y = self.y * GRID_SIZE + GRID_SIZE // 2
        
        # Draw shadow
        shadow_offset = 3
        pygame.draw.circle(screen, (0, 0, 0, 50), 
                         (apple_x + shadow_offset, apple_y + shadow_offset), size//2)
        
        # Draw apple with gradient effect
        for i in range(size//2, 0, -1):
            brightness = 1 - (i / (size//2)) * 0.3
            color = (int(COLORS['APPLE_RED'][0] * brightness),
                    int(COLORS['APPLE_RED'][1] * brightness),
                    int(COLORS['APPLE_RED'][2] * brightness))
            pygame.draw.circle(screen, color, (apple_x, apple_y), i)
        
        # Draw highlight
        highlight_size = max(2, size // 4)
        highlight_x = apple_x - size // 4
        highlight_y = apple_y - size // 4
        pygame.draw.circle(screen, COLORS['APPLE_HIGHLIGHT'], 
                         (highlight_x, highlight_y), highlight_size)
        
        # Draw sparkles
        for sparkle in self.sparkle_particles:
            alpha = int(255 * sparkle['life'])
            sparkle_size = max(1, int(3 * sparkle['life']))
            pygame.draw.circle(screen, (255, 255, 0), 
                             (int(sparkle['x']), int(sparkle['y'])), sparkle_size)

class Obstacle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.damage_level = 0
        
    def draw(self, screen):
        # Rock-like obstacle with 3D effect
        obstacle_x = self.x * GRID_SIZE
        obstacle_y = self.y * GRID_SIZE
        
        # Draw shadow
        shadow_rect = pygame.Rect(obstacle_x + 2, obstacle_y + 2, GRID_SIZE, GRID_SIZE)
        pygame.draw.rect(screen, (0, 0, 0, 80), shadow_rect)
        
        # Draw multiple layers for 3D effect
        for layer in range(3):
            offset = layer * 2
            layer_rect = pygame.Rect(obstacle_x + offset, obstacle_y + offset, 
                                   GRID_SIZE - offset*2, GRID_SIZE - offset*2)
            
            if layer == 0:
                color = COLORS['OBSTACLE_DARK']
            elif layer == 1:
                color = COLORS['OBSTACLE_BROWN']
            else:
                color = (160, 90, 40)  # Lighter brown
                
            pygame.draw.rect(screen, color, layer_rect)
            pygame.draw.rect(screen, (0, 0, 0), layer_rect, 1)
        
        # Add texture details
        for i in range(3):
            detail_x = obstacle_x + random.randint(2, GRID_SIZE-4)
            detail_y = obstacle_y + random.randint(2, GRID_SIZE-4)
            pygame.draw.circle(screen, COLORS['OBSTACLE_DARK'], 
                             (detail_x, detail_y), 1)

class Snake:
    def __init__(self, start_x, start_y):
        self.segments = [SnakeSegment(start_x, start_y, True)]
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.growing = False
        self.move_timer = 0
        self.move_delay = 0.15  # Smooth movement timing
        
    def update(self, dt):
        self.move_timer += dt
        
        # Update smooth positions for all segments
        for segment in self.segments:
            segment.update_smooth_position(0.3)
        
        if self.move_timer >= self.move_delay:
            self.move_timer = 0
            self.move()
    
    def set_direction(self, direction):
        # Prevent immediate reversal
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
        
        # Store previous positions
        for segment in self.segments:
            segment.prev_x = segment.x
            segment.prev_y = segment.y
        
        # Move head
        head = self.segments[0]
        dx, dy = self.direction.value
        head.x += dx
        head.y += dy
        
        # Move body segments
        for i in range(1, len(self.segments)):
            self.segments[i].x = self.segments[i-1].prev_x
            self.segments[i].y = self.segments[i-1].prev_y
        
        # Handle growing
        if self.growing:
            tail = self.segments[-1]
            new_segment = SnakeSegment(tail.prev_x, tail.prev_y)
            self.segments.append(new_segment)
            self.growing = False
    
    def grow(self):
        self.growing = True
    
    def get_head_position(self):
        return (self.segments[0].x, self.segments[0].y)
    
    def check_collision(self, x, y):
        return any(segment.x == x and segment.y == y for segment in self.segments)
    
    def check_wall_collision(self):
        head_x, head_y = self.get_head_position()
        return (head_x < 0 or head_x >= GRID_WIDTH or 
                head_y < 0 or head_y >= GRID_HEIGHT)
    
    def check_self_collision(self):
        head_pos = self.get_head_position()
        return any(segment.x == head_pos[0] and segment.y == head_pos[1] 
                  for segment in self.segments[1:])
    
    def draw(self, screen):
        # Draw snake with realistic segments
        for i, segment in enumerate(self.segments):
            x = int(segment.smooth_x)
            y = int(segment.smooth_y)
            
            if segment.is_head:
                # Draw head with eyes and detailed features
                self.draw_head(screen, x, y)
            else:
                # Draw body segment with scales
                self.draw_body_segment(screen, x, y, i)
    
    def draw_head(self, screen, x, y):
        head_rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
        
        # Draw shadow
        shadow_rect = pygame.Rect(x + 2, y + 2, GRID_SIZE, GRID_SIZE)
        pygame.draw.ellipse(screen, (0, 0, 0, 100), shadow_rect)
        
        # Draw head base
        pygame.draw.ellipse(screen, COLORS['SNAKE_HEAD'], head_rect)
        pygame.draw.ellipse(screen, (0, 0, 0), head_rect, 2)
        
        # Draw eyes based on direction
        eye_size = 3
        if self.direction == Direction.RIGHT:
            eye1_pos = (x + GRID_SIZE - 8, y + 5)
            eye2_pos = (x + GRID_SIZE - 8, y + GRID_SIZE - 8)
        elif self.direction == Direction.LEFT:
            eye1_pos = (x + 5, y + 5)
            eye2_pos = (x + 5, y + GRID_SIZE - 8)
        elif self.direction == Direction.UP:
            eye1_pos = (x + 5, y + 5)
            eye2_pos = (x + GRID_SIZE - 8, y + 5)
        else:  # DOWN
            eye1_pos = (x + 5, y + GRID_SIZE - 8)
            eye2_pos = (x + GRID_SIZE - 8, y + GRID_SIZE - 8)
        
        # Draw eyes
        pygame.draw.circle(screen, COLORS['WHITE'], eye1_pos, eye_size)
        pygame.draw.circle(screen, COLORS['WHITE'], eye2_pos, eye_size)
        pygame.draw.circle(screen, COLORS['BLACK'], eye1_pos, eye_size - 1)
        pygame.draw.circle(screen, COLORS['BLACK'], eye2_pos, eye_size - 1)
        
        # Draw nostrils
        nostril_color = (40, 60, 40)
        if self.direction == Direction.RIGHT:
            nostril_pos = (x + GRID_SIZE - 4, y + GRID_SIZE // 2)
        elif self.direction == Direction.LEFT:
            nostril_pos = (x + 2, y + GRID_SIZE // 2)
        elif self.direction == Direction.UP:
            nostril_pos = (x + GRID_SIZE // 2, y + 2)
        else:  # DOWN
            nostril_pos = (x + GRID_SIZE // 2, y + GRID_SIZE - 4)
        
        pygame.draw.circle(screen, nostril_color, nostril_pos, 1)
    
    def draw_body_segment(self, screen, x, y, segment_index):
        segment_rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
        
        # Draw shadow
        shadow_rect = pygame.Rect(x + 1, y + 1, GRID_SIZE, GRID_SIZE)
        pygame.draw.ellipse(screen, (0, 0, 0, 60), shadow_rect)
        
        # Alternate colors for realistic pattern
        if segment_index % 2 == 0:
            color = COLORS['SNAKE_BODY']
        else:
            color = COLORS['SNAKE_BELLY']
        
        # Draw main body
        pygame.draw.ellipse(screen, color, segment_rect)
        pygame.draw.ellipse(screen, (0, 0, 0), segment_rect, 1)
        
        # Draw scale details
        for scale_row in range(2):
            for scale_col in range(3):
                scale_x = x + 4 + scale_col * 4
                scale_y = y + 4 + scale_row * 6
                scale_color = (color[0] - 20, color[1] - 20, color[2] - 20)
                pygame.draw.circle(screen, scale_color, (scale_x, scale_y), 1)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Ultra Realistic Snake Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
        
        self.reset_game()
        self.particle_system = ParticleSystem()
        
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
        while True:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            
            # Check if position is free
            if not self.snake.check_collision(x, y) and not self.is_obstacle(x, y):
                self.apple = Apple(x, y)
                break
    
    def spawn_obstacles(self):
        obstacle_count = min(10, (self.apples_eaten // 5) * 2 + 2)
        
        for _ in range(obstacle_count):
            attempts = 0
            while attempts < 50:  # Prevent infinite loop
                x = random.randint(0, GRID_WIDTH - 1)
                y = random.randint(0, GRID_HEIGHT - 1)
                
                if (not self.snake.check_collision(x, y) and 
                    not self.is_obstacle(x, y) and 
                    (x != self.apple.x or y != self.apple.y)):
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
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_r and self.game_over:
                    self.reset_game()
                elif event.key == pygame.K_SPACE:
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
        
        self.snake.update(dt)
        
        if self.apple:
            self.apple.update(dt)
        
        self.particle_system.update(dt)
        
        # Check apple collision
        head_pos = self.snake.get_head_position()
        if self.apple and head_pos[0] == self.apple.x and head_pos[1] == self.apple.y:
            # Apple eaten
            self.snake.grow()
            self.score += 10
            self.apples_eaten += 1
            
            # Add explosion effect
            apple_pixel_x = self.apple.x * GRID_SIZE + GRID_SIZE // 2
            apple_pixel_y = self.apple.y * GRID_SIZE + GRID_SIZE // 2
            self.particle_system.add_explosion(apple_pixel_x, apple_pixel_y, 
                                             COLORS['APPLE_RED'], 20)
            
            # Spawn new apple
            self.spawn_apple()
            
            # Add obstacles every 5 apples
            if self.apples_eaten % 5 == 0:
                self.spawn_obstacles()
                # Speed up snake slightly
                self.snake.move_delay = max(0.08, self.snake.move_delay - 0.01)
        
        # Check collisions
        head_x, head_y = head_pos
        
        # Wall collision
        if self.snake.check_wall_collision():
            self.game_over = True
            self.particle_system.add_explosion(head_x * GRID_SIZE + GRID_SIZE//2,
                                             head_y * GRID_SIZE + GRID_SIZE//2,
                                             COLORS['SNAKE_HEAD'], 30)
        
        # Self collision
        if self.snake.check_self_collision():
            self.game_over = True
            self.particle_system.add_explosion(head_x * GRID_SIZE + GRID_SIZE//2,
                                             head_y * GRID_SIZE + GRID_SIZE//2,
                                             COLORS['SNAKE_HEAD'], 30)
        
        # Obstacle collision
        if self.is_obstacle(head_x, head_y):
            self.game_over = True
            self.particle_system.add_explosion(head_x * GRID_SIZE + GRID_SIZE//2,
                                             head_y * GRID_SIZE + GRID_SIZE//2,
                                             COLORS['OBSTACLE_BROWN'], 30)
    
    def draw_grid(self):
        for x in range(0, WINDOW_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, COLORS['GRID_LINE'], 
                           (x, 0), (x, WINDOW_HEIGHT), 1)
        for y in range(0, WINDOW_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, COLORS['GRID_LINE'], 
                           (0, y), (WINDOW_WIDTH, y), 1)
    
    def draw_ui(self):
        # Score
        score_text = self.font.render(f"Score: {self.score}", True, COLORS['UI_GREEN'])
        self.screen.blit(score_text, (10, 10))
        
        # Apples eaten
        apples_text = self.font.render(f"Apples: {self.apples_eaten}", True, COLORS['UI_GREEN'])
        self.screen.blit(apples_text, (10, 50))
        
        # Speed indicator
        speed_text = self.font.render(f"Speed: {1/self.snake.move_delay:.1f}", True, COLORS['UI_GREEN'])
        self.screen.blit(speed_text, (10, 90))
        
        # Obstacles count
        obs_text = self.font.render(f"Obstacles: {len(self.obstacles)}", True, COLORS['UI_GREEN'])
        self.screen.blit(obs_text, (10, 130))
        
        if self.paused:
            pause_text = self.big_font.render("PAUSED", True, COLORS['WHITE'])
            text_rect = pause_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
            self.screen.blit(pause_text, text_rect)
        
        if self.game_over:
            game_over_text = self.big_font.render("GAME OVER", True, COLORS['APPLE_RED'])
            restart_text = self.font.render("Press R to restart", True, COLORS['WHITE'])
            
            go_rect = game_over_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 50))
            r_rect = restart_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 20))
            
            self.screen.blit(game_over_text, go_rect)
            self.screen.blit(restart_text, r_rect)
        
        # Controls
        controls = [
            "WASD/Arrow Keys: Move",
            "Space: Pause",
            "R: Restart (when game over)",
            "ESC: Quit"
        ]
        
        for i, control in enumerate(controls):
            text = pygame.font.Font(None, 24).render(control, True, COLORS['WHITE'])
            self.screen.blit(text, (WINDOW_WIDTH - 250, 10 + i * 25))
    
    def draw(self):
        # Background gradient
        for y in range(WINDOW_HEIGHT):
            color_factor = y / WINDOW_HEIGHT
            r = int(COLORS['DARK_GREEN'][0] * (1 - color_factor * 0.3))
            g = int(COLORS['DARK_GREEN'][1] * (1 - color_factor * 0.3))
            b = int(COLORS['DARK_GREEN'][2] * (1 - color_factor * 0.3))
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WINDOW_WIDTH, y))
        
        self.draw_grid()
        
        # Draw obstacles
        for obstacle in self.obstacles:
            obstacle.draw(self.screen)
        
        # Draw apple
        if self.apple:
            self.apple.draw(self.screen)
        
        # Draw snake
        self.snake.draw(self.screen)
        
        # Draw particles
        self.particle_system.draw(self.screen)
        
        # Draw UI
        self.draw_ui()
    
    def run(self):
        running = True
        last_time = time.time()
        
        while running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            running = self.handle_events()
            self.update(dt)
            self.draw()
            
            pygame.display.flip()
            self.clock.tick(60)  # 60 FPS for smooth animation
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()