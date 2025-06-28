#!/usr/bin/env python3
"""
Retro Snake Game - Raspberry Pi Edition
A modern take on the classic Snake game with power-ups, obstacles, and sleek graphics
Optimized for Raspberry Pi Zero 2W
"""

import pygame
import random
import math
import sys
import time
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple, Optional

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
GRID_SIZE = 20
GRID_WIDTH = WINDOW_WIDTH // GRID_SIZE
GRID_HEIGHT = WINDOW_HEIGHT // GRID_SIZE

# Colors - Retro neon palette
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
NEON_GREEN = (57, 255, 20)
NEON_PINK = (255, 20, 147)
NEON_BLUE = (30, 144, 255)
NEON_YELLOW = (255, 255, 0)
NEON_ORANGE = (255, 165, 0)
NEON_PURPLE = (138, 43, 226)
NEON_CYAN = (0, 255, 255)
DARK_GRAY = (40, 40, 40)
LIGHT_GRAY = (128, 128, 128)
RED = (255, 0, 0)

# Game states
class GameState(Enum):
    MENU = 1
    PLAYING = 2
    PAUSED = 3
    GAME_OVER = 4

# Directions
class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

# Power-up types
class PowerUpType(Enum):
    SPEED_BOOST = 1
    SLOW_DOWN = 2
    GROW = 3
    SHRINK = 4
    INVINCIBILITY = 5
    DOUBLE_POINTS = 6

@dataclass
class PowerUp:
    x: int
    y: int
    type: PowerUpType
    duration: int
    color: Tuple[int, int, int]
    spawn_time: float

@dataclass
class Obstacle:
    x: int
    y: int
    width: int
    height: int
    color: Tuple[int, int, int]
    pattern: str

class Particle:
    def __init__(self, x, y, color, velocity, lifetime=60):
        self.x = x
        self.y = y
        self.color = color
        self.velocity = velocity
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = random.randint(2, 5)
    
    def update(self):
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        self.lifetime -= 1
        self.velocity = (self.velocity[0] * 0.98, self.velocity[1] * 0.98)
    
    def draw(self, screen):
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        color_with_alpha = (*self.color, alpha)
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, color_with_alpha, (self.size, self.size), self.size)
        screen.blit(s, (self.x - self.size, self.y - self.size))

class SnakeGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Retro Snake - Raspberry Pi Edition")
        self.clock = pygame.time.Clock()
        self.font_small = pygame.font.Font(None, 24)
        self.font_medium = pygame.font.Font(None, 36)
        self.font_large = pygame.font.Font(None, 48)
        self.font_title = pygame.font.Font(None, 72)
        
        self.reset_game()
        self.state = GameState.MENU
        self.particles = []
        self.screen_shake = 0
        self.background_pattern = self.create_background_pattern()
        
    def create_background_pattern(self):
        """Create a retro grid background pattern"""
        pattern = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        pattern.fill(BLACK)
        
        # Draw grid lines
        for x in range(0, WINDOW_WIDTH, GRID_SIZE):
            pygame.draw.line(pattern, (10, 10, 20), (x, 0), (x, WINDOW_HEIGHT), 1)
        for y in range(0, WINDOW_HEIGHT, GRID_SIZE):
            pygame.draw.line(pattern, (10, 10, 20), (0, y), (WINDOW_WIDTH, y), 1)
            
        return pattern
    
    def reset_game(self):
        """Reset game to initial state"""
        self.snake = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = Direction.RIGHT
        self.food = self.spawn_food()
        self.score = 0
        self.high_score = self.load_high_score()
        self.speed = 8
        self.base_speed = 8
        self.power_ups = []
        self.obstacles = []
        self.active_effects = {}
        self.effect_timers = {}
        self.invincible = False
        self.double_points = False
        self.game_time = 0
        self.level = 1
        
        self.generate_obstacles()
        
    def load_high_score(self):
        """Load high score from file"""
        try:
            with open('snake_highscore.txt', 'r') as f:
                return int(f.read().strip())
        except:
            return 0
    
    def save_high_score(self):
        """Save high score to file"""
        try:
            with open('snake_highscore.txt', 'w') as f:
                f.write(str(self.high_score))
        except:
            pass
    
    def spawn_food(self):
        """Spawn food at random location avoiding snake and obstacles"""
        while True:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            
            # Check if position is free
            if (x, y) not in self.snake and not self.is_obstacle_at(x, y):
                return (x, y)
    
    def spawn_power_up(self):
        """Spawn a random power-up"""
        if len(self.power_ups) >= 3:  # Limit power-ups on screen
            return
            
        power_up_types = [
            (PowerUpType.SPEED_BOOST, NEON_YELLOW),
            (PowerUpType.SLOW_DOWN, NEON_BLUE),
            (PowerUpType.GROW, NEON_GREEN),
            (PowerUpType.SHRINK, NEON_PINK),
            (PowerUpType.INVINCIBILITY, NEON_PURPLE),
            (PowerUpType.DOUBLE_POINTS, NEON_ORANGE)
        ]
        
        power_type, color = random.choice(power_up_types)
        
        while True:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            
            if (x, y) not in self.snake and (x, y) != self.food and not self.is_obstacle_at(x, y):
                power_up = PowerUp(x, y, power_type, 300, color, time.time())
                self.power_ups.append(power_up)
                break
    
    def generate_obstacles(self):
        """Generate obstacles based on current level"""
        self.obstacles.clear()
        
        obstacle_count = min(3 + self.level // 2, 8)
        
        for _ in range(obstacle_count):
            self.create_random_obstacle()
    
    def create_random_obstacle(self):
        """Create a random obstacle pattern"""
        patterns = ['line', 'box', 'cross', 'corner']
        pattern = random.choice(patterns)
        
        if pattern == 'line':
            self.create_line_obstacle()
        elif pattern == 'box':
            self.create_box_obstacle()
        elif pattern == 'cross':
            self.create_cross_obstacle()
        elif pattern == 'corner':
            self.create_corner_obstacle()
    
    def create_line_obstacle(self):
        """Create a line obstacle"""
        horizontal = random.choice([True, False])
        if horizontal:
            length = random.randint(3, 8)
            x = random.randint(2, GRID_WIDTH - length - 2)
            y = random.randint(2, GRID_HEIGHT - 2)
            self.obstacles.append(Obstacle(x, y, length, 1, LIGHT_GRAY, 'line'))
        else:
            length = random.randint(3, 6)
            x = random.randint(2, GRID_WIDTH - 2)
            y = random.randint(2, GRID_HEIGHT - length - 2)
            self.obstacles.append(Obstacle(x, y, 1, length, LIGHT_GRAY, 'line'))
    
    def create_box_obstacle(self):
        """Create a box obstacle"""
        size = random.randint(2, 4)
        x = random.randint(2, GRID_WIDTH - size - 2)
        y = random.randint(2, GRID_HEIGHT - size - 2)
        self.obstacles.append(Obstacle(x, y, size, size, DARK_GRAY, 'box'))
    
    def create_cross_obstacle(self):
        """Create a cross-shaped obstacle"""
        x = random.randint(3, GRID_WIDTH - 4)
        y = random.randint(3, GRID_HEIGHT - 4)
        # Cross pattern implemented as multiple small obstacles
        self.obstacles.append(Obstacle(x, y-1, 1, 3, NEON_CYAN, 'cross'))
        self.obstacles.append(Obstacle(x-1, y, 3, 1, NEON_CYAN, 'cross'))
    
    def create_corner_obstacle(self):
        """Create an L-shaped corner obstacle"""
        x = random.randint(2, GRID_WIDTH - 4)
        y = random.randint(2, GRID_HEIGHT - 4)
        self.obstacles.append(Obstacle(x, y, 3, 1, NEON_PINK, 'corner'))
        self.obstacles.append(Obstacle(x, y, 1, 3, NEON_PINK, 'corner'))
    
    def is_obstacle_at(self, x, y):
        """Check if there's an obstacle at given position"""
        for obstacle in self.obstacles:
            if (obstacle.x <= x < obstacle.x + obstacle.width and 
                obstacle.y <= y < obstacle.y + obstacle.height):
                return True
        return False
    
    def handle_input(self):
        """Handle keyboard input"""
        keys = pygame.key.get_pressed()
        
        if self.state == GameState.PLAYING:
            if keys[pygame.K_UP] and self.direction != Direction.DOWN:
                self.direction = Direction.UP
            elif keys[pygame.K_DOWN] and self.direction != Direction.UP:
                self.direction = Direction.DOWN
            elif keys[pygame.K_LEFT] and self.direction != Direction.RIGHT:
                self.direction = Direction.LEFT
            elif keys[pygame.K_RIGHT] and self.direction != Direction.LEFT:
                self.direction = Direction.RIGHT
            elif keys[pygame.K_SPACE]:
                self.state = GameState.PAUSED
        
        elif self.state == GameState.PAUSED:
            if keys[pygame.K_SPACE]:
                self.state = GameState.PLAYING
        
        elif self.state == GameState.MENU:
            if keys[pygame.K_SPACE]:
                self.reset_game()
                self.state = GameState.PLAYING
        
        elif self.state == GameState.GAME_OVER:
            if keys[pygame.K_SPACE]:
                self.state = GameState.MENU
    
    def update_game(self):
        """Update game logic"""
        if self.state != GameState.PLAYING:
            return
        
        self.game_time += 1
        
        # Update power-up effects
        self.update_effects()
        
        # Spawn power-ups occasionally
        if random.randint(1, 200) == 1:
            self.spawn_power_up()
        
        # Remove expired power-ups
        current_time = time.time()
        self.power_ups = [p for p in self.power_ups 
                         if current_time - p.spawn_time < 10]
        
        # Move snake
        head_x, head_y = self.snake[0]
        dx, dy = self.direction.value
        new_head = (head_x + dx, head_y + dy)
        
        # Check collisions
        if self.check_collision(new_head):
            if not self.invincible:
                self.game_over()
                return
        
        self.snake.insert(0, new_head)
        
        # Check food collision
        if new_head == self.food:
            points = 10
            if self.double_points:
                points *= 2
            self.score += points
            self.food = self.spawn_food()
            
            # Create particles
            self.create_food_particles(new_head)
            
            # Level up every 100 points
            if self.score // 100 > self.level - 1:
                self.level_up()
        else:
            self.snake.pop()
        
        # Check power-up collision
        for power_up in self.power_ups[:]:
            if new_head == (power_up.x, power_up.y):
                self.apply_power_up(power_up)
                self.power_ups.remove(power_up)
                self.create_power_up_particles((power_up.x, power_up.y), power_up.color)
    
    def check_collision(self, pos):
        """Check if position collides with walls, snake, or obstacles"""
        x, y = pos
        
        # Wall collision
        if x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT:
            return True
        
        # Self collision
        if pos in self.snake:
            return True
        
        # Obstacle collision
        if self.is_obstacle_at(x, y):
            return True
        
        return False
    
    def apply_power_up(self, power_up):
        """Apply power-up effect"""
        effect_duration = 300  # frames
        
        if power_up.type == PowerUpType.SPEED_BOOST:
            self.speed = min(self.speed + 3, 20)
            self.effect_timers['speed_boost'] = effect_duration
        
        elif power_up.type == PowerUpType.SLOW_DOWN:
            self.speed = max(self.speed - 2, 3)
            self.effect_timers['slow_down'] = effect_duration
        
        elif power_up.type == PowerUpType.GROW:
            for _ in range(3):
                if self.snake:
                    tail = self.snake[-1]
                    self.snake.append(tail)
        
        elif power_up.type == PowerUpType.SHRINK:
            if len(self.snake) > 3:
                for _ in range(min(2, len(self.snake) - 1)):
                    self.snake.pop()
        
        elif power_up.type == PowerUpType.INVINCIBILITY:
            self.invincible = True
            self.effect_timers['invincibility'] = effect_duration
        
        elif power_up.type == PowerUpType.DOUBLE_POINTS:
            self.double_points = True
            self.effect_timers['double_points'] = effect_duration
        
        self.score += 5  # Bonus points for collecting power-up
    
    def update_effects(self):
        """Update active power-up effects"""
        for effect, timer in list(self.effect_timers.items()):
            self.effect_timers[effect] = timer - 1
            
            if timer <= 0:
                if effect == 'speed_boost':
                    self.speed = self.base_speed
                elif effect == 'slow_down':
                    self.speed = self.base_speed
                elif effect == 'invincibility':
                    self.invincible = False
                elif effect == 'double_points':
                    self.double_points = False
                
                del self.effect_timers[effect]
    
    def level_up(self):
        """Increase level and difficulty"""
        self.level += 1
        self.base_speed = min(self.base_speed + 1, 15)
        self.speed = self.base_speed
        self.generate_obstacles()
        
        # Screen shake effect
        self.screen_shake = 10
        
        # Create celebration particles
        for _ in range(20):
            self.create_random_particle((WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
    
    def create_food_particles(self, pos):
        """Create particles when food is eaten"""
        x, y = pos[0] * GRID_SIZE + GRID_SIZE // 2, pos[1] * GRID_SIZE + GRID_SIZE // 2
        for _ in range(8):
            velocity = (random.uniform(-3, 3), random.uniform(-3, 3))
            self.particles.append(Particle(x, y, NEON_GREEN, velocity))
    
    def create_power_up_particles(self, pos, color):
        """Create particles when power-up is collected"""
        x, y = pos[0] * GRID_SIZE + GRID_SIZE // 2, pos[1] * GRID_SIZE + GRID_SIZE // 2
        for _ in range(12):
            velocity = (random.uniform(-4, 4), random.uniform(-4, 4))
            self.particles.append(Particle(x, y, color, velocity))
    
    def create_random_particle(self, pos):
        """Create a random colored particle"""
        colors = [NEON_GREEN, NEON_PINK, NEON_BLUE, NEON_YELLOW, NEON_ORANGE]
        color = random.choice(colors)
        velocity = (random.uniform(-5, 5), random.uniform(-5, 5))
        self.particles.append(Particle(pos[0], pos[1], color, velocity))
    
    def game_over(self):
        """Handle game over"""
        self.state = GameState.GAME_OVER
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()
        
        # Create explosion particles
        head = self.snake[0]
        x, y = head[0] * GRID_SIZE + GRID_SIZE // 2, head[1] * GRID_SIZE + GRID_SIZE // 2
        for _ in range(30):
            velocity = (random.uniform(-6, 6), random.uniform(-6, 6))
            self.particles.append(Particle(x, y, RED, velocity, 120))
    
    def draw_snake(self):
        """Draw the snake with gradient effect"""
        for i, (x, y) in enumerate(self.snake):
            rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            
            if i == 0:  # Head
                color = NEON_GREEN if not self.invincible else NEON_PURPLE
                # Add glowing effect for head
                glow_rect = rect.inflate(4, 4)
                pygame.draw.rect(self.screen, (*color, 100), glow_rect)
            else:  # Body
                # Gradient from head to tail
                intensity = max(50, 255 - i * 10)
                color = (0, intensity, 0) if not self.invincible else (intensity, 0, intensity)
            
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, WHITE, rect, 1)
    
    def draw_food(self):
        """Draw food with pulsing effect"""
        x, y = self.food
        rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
        
        # Pulsing effect
        pulse = int(128 + 127 * math.sin(self.game_time * 0.3))
        color = (255, pulse, pulse)
        
        # Glow effect
        glow_rect = rect.inflate(6, 6)
        pygame.draw.rect(self.screen, (*color, 80), glow_rect)
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, WHITE, rect, 2)
    
    def draw_power_ups(self):
        """Draw power-ups with special effects"""
        current_time = time.time()
        
        for power_up in self.power_ups:
            x, y = power_up.x * GRID_SIZE, power_up.y * GRID_SIZE
            rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
            
            # Blinking effect when about to expire
            time_left = 10 - (current_time - power_up.spawn_time)
            if time_left < 3 and int(current_time * 10) % 2:
                continue
            
            # Rotating effect
            angle = self.game_time * 5
            
            # Draw rotating square
            center = rect.center
            points = []
            for i in range(4):
                px = center[0] + (GRID_SIZE // 3) * math.cos(math.radians(angle + i * 90))
                py = center[1] + (GRID_SIZE // 3) * math.sin(math.radians(angle + i * 90))
                points.append((px, py))
            
            pygame.draw.polygon(self.screen, power_up.color, points)
            pygame.draw.polygon(self.screen, WHITE, points, 2)
    
    def draw_obstacles(self):
        """Draw obstacles with neon effects"""
        for obstacle in self.obstacles:
            for ox in range(obstacle.width):
                for oy in range(obstacle.height):
                    x = (obstacle.x + ox) * GRID_SIZE
                    y = (obstacle.y + oy) * GRID_SIZE
                    rect = pygame.Rect(x, y, GRID_SIZE, GRID_SIZE)
                    
                    # Glow effect
                    glow_rect = rect.inflate(2, 2)
                    pygame.draw.rect(self.screen, (*obstacle.color, 100), glow_rect)
                    pygame.draw.rect(self.screen, obstacle.color, rect)
                    pygame.draw.rect(self.screen, WHITE, rect, 1)
    
    def draw_hud(self):
        """Draw heads-up display"""
        # Score
        score_text = self.font_medium.render(f"Score: {self.score}", True, NEON_GREEN)
        self.screen.blit(score_text, (10, 10))
        
        # High Score
        high_score_text = self.font_small.render(f"High: {self.high_score}", True, NEON_YELLOW)
        self.screen.blit(high_score_text, (10, 45))
        
        # Level
        level_text = self.font_small.render(f"Level: {self.level}", True, NEON_BLUE)
        self.screen.blit(level_text, (10, 70))
        
        # Speed
        speed_text = self.font_small.render(f"Speed: {self.speed}", True, NEON_CYAN)
        self.screen.blit(speed_text, (10, 95))
        
        # Active effects
        y_offset = 120
        for effect, timer in self.effect_timers.items():
            effect_name = effect.replace('_', ' ').title()
            color = NEON_PURPLE if effect == 'invincibility' else NEON_ORANGE
            effect_text = self.font_small.render(f"{effect_name}: {timer//60}s", True, color)
            self.screen.blit(effect_text, (10, y_offset))
            y_offset += 25
    
    def draw_menu(self):
        """Draw main menu"""
        # Title with glow effect
        title_text = self.font_title.render("RETRO SNAKE", True, NEON_GREEN)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 150))
        
        # Glow effect
        for offset in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
            glow_text = self.font_title.render("RETRO SNAKE", True, (0, 100, 0))
            glow_rect = title_rect.copy()
            glow_rect.move_ip(offset)
            self.screen.blit(glow_text, glow_rect)
        
        self.screen.blit(title_text, title_rect)
        
        # Instructions
        instructions = [
            "Use Arrow Keys to Move",
            "Collect Food and Power-ups",
            "Avoid Obstacles and Yourself",
            "",
            f"High Score: {self.high_score}",
            "",
            "Press SPACE to Start"
        ]
        
        y_offset = 250
        for instruction in instructions:
            if instruction:
                color = NEON_YELLOW if "High Score" in instruction else NEON_CYAN
                if "Press SPACE" in instruction:
                    color = NEON_PINK
                    # Blinking effect
                    if int(time.time() * 3) % 2 == 0:
                        color = WHITE
                
                text = self.font_medium.render(instruction, True, color)
                text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, y_offset))
                self.screen.blit(text, text_rect)
            
            y_offset += 35
    
    def draw_game_over(self):
        """Draw game over screen"""
        # Game Over text
        game_over_text = self.font_large.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, 200))
        self.screen.blit(game_over_text, game_over_rect)
        
        # Final score
        score_text = self.font_medium.render(f"Final Score: {self.score}", True, NEON_GREEN)
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, 280))
        self.screen.blit(score_text, score_rect)
        
        # High score
        if self.score == self.high_score and self.score > 0:
            new_high_text = self.font_medium.render("NEW HIGH SCORE!", True, NEON_YELLOW)
            new_high_rect = new_high_text.get_rect(center=(WINDOW_WIDTH // 2, 320))
            self.screen.blit(new_high_text, new_high_rect)
        
        # Continue instruction
        continue_text = self.font_medium.render("Press SPACE to Continue", True, NEON_PINK)
        continue_rect = continue_text.get_rect(center=(WINDOW_WIDTH // 2, 400))
        
        # Blinking effect
        if int(time.time() * 3) % 2 == 0:
            self.screen.blit(continue_text, continue_rect)
    
    def draw_pause_screen(self):
        """Draw pause screen overlay"""
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Pause text
        pause_text = self.font_large.render("PAUSED", True, NEON_YELLOW)
        pause_rect = pause_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        self.screen.blit(pause_text, pause_rect)
        
        # Continue instruction
        continue_text = self.font_medium.render("Press SPACE to Continue", True, NEON_CYAN)
        continue_rect = continue_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20))
        self.screen.blit(continue_text, continue_rect)
    
    def update_particles(self):
        """Update and remove expired particles"""
        for particle in self.particles[:]:
            particle.update()
            if particle.lifetime <= 0:
                self.particles.remove(particle)
    
    def draw_particles(self):
        """Draw all particles"""
        for particle in self.particles:
            particle.draw(self.screen)
    
    def apply_screen_shake(self):
        """Apply screen shake effect"""
        if self.screen_shake > 0:
            shake_x = random.randint(-self.screen_shake, self.screen_shake)
            shake_y = random.randint(-self.screen_shake, self.screen_shake)
            self.screen.scroll(shake_x, shake_y)
            self.screen_shake -= 1
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == GameState.PLAYING:
                            self.state = GameState.PAUSED
                        elif self.state == GameState.PAUSED:
                            self.state = GameState.MENU
                        else:
                            running = False
            
            # Handle continuous input
            self.handle_input()
            
            # Update game
            self.update_game()
            self.update_particles()
            
            # Draw everything
            self.screen.blit(self.background_pattern, (0, 0))
            
            if self.state == GameState.PLAYING:
                self.draw_obstacles()
                self.draw_food()
                self.draw_power_ups()
                self.draw_snake()
                self.draw_hud()
                
            elif self.state == GameState.MENU:
                self.draw_menu()
                
            elif self.state == GameState.GAME_OVER:
                # Still show game elements in background
                self.draw_obstacles()
                self.draw_snake()
                self.draw_game_over()
                
            elif self.state == GameState.PAUSED:
                self.draw_obstacles()
                self.draw_food()
                self.draw_power_ups()
                self.draw_snake()
                self.draw_hud()
                self.draw_pause_screen()
            
            # Always draw particles on top
            self.draw_particles()
            
            # Apply screen effects
            self.apply_screen_shake()
            
            # Update display
            pygame.display.flip()
            self.clock.tick(self.speed if self.state == GameState.PLAYING else 60)
        
        pygame.quit()
        sys.exit()

# Additional utility functions for enhanced gameplay
class GameEffects:
    """Class to handle advanced visual effects"""
    
    @staticmethod
    def create_trail_effect(screen, positions, color, max_alpha=255):
        """Create a trailing effect for moving objects"""
        for i, pos in enumerate(positions):
            alpha = max_alpha * (i + 1) / len(positions)
            trail_surface = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
            trail_color = (*color, int(alpha))
            pygame.draw.rect(trail_surface, trail_color, (0, 0, GRID_SIZE, GRID_SIZE))
            screen.blit(trail_surface, (pos[0] * GRID_SIZE, pos[1] * GRID_SIZE))
    
    @staticmethod
    def draw_neon_border(screen, rect, color, thickness=2):
        """Draw a neon-style glowing border"""
        # Outer glow
        for i in range(thickness * 2):
            glow_rect = rect.inflate(i * 2, i * 2)
            glow_alpha = max(10, 100 - i * 15)
            glow_surface = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*color, glow_alpha), glow_surface.get_rect(), 1)
            screen.blit(glow_surface, glow_rect.topleft)
        
        # Main border
        pygame.draw.rect(screen, color, rect, thickness)

class SoundManager:
    """Handle game sounds and music (placeholder for future implementation)"""
    
    def __init__(self):
        self.enabled = True
        
    def play_sound(self, sound_name):
        """Play a sound effect"""
        if not self.enabled:
            return
        # Placeholder for sound implementation
        pass
    
    def play_music(self, music_name):
        """Play background music"""
        if not self.enabled:
            return
        # Placeholder for music implementation
        pass

class AIPlayer:
    """Simple AI player for demonstration purposes"""
    
    def __init__(self, game):
        self.game = game
        
    def get_next_move(self):
        """Calculate the next optimal move"""
        if not self.game.snake:
            return Direction.RIGHT
            
        head = self.game.snake[0]
        food = self.game.food
        
        # Simple pathfinding toward food
        dx = food[0] - head[0]
        dy = food[1] - head[1]
        
        # Prioritize the direction with larger distance
        if abs(dx) > abs(dy):
            if dx > 0:
                return Direction.RIGHT
            else:
                return Direction.LEFT
        else:
            if dy > 0:
                return Direction.DOWN
            else:
                return Direction.UP

class GameStats:
    """Track detailed game statistics"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.games_played = 0
        self.total_score = 0
        self.total_time = 0
        self.power_ups_collected = 0
        self.max_length = 0
        self.levels_completed = 0
    
    def update_game_end(self, score, time_played, snake_length, level):
        self.games_played += 1
        self.total_score += score
        self.total_time += time_played
        self.max_length = max(self.max_length, snake_length)
        self.levels_completed = max(self.levels_completed, level)
    
    def get_average_score(self):
        return self.total_score / max(1, self.games_played)

# Enhanced power-up system
class PowerUpManager:
    """Manage complex power-up interactions"""
    
    def __init__(self):
        self.combo_multiplier = 1.0
        self.last_power_up_time = 0
        
    def calculate_combo_bonus(self, current_time):
        """Calculate combo bonus for collecting power-ups quickly"""
        time_diff = current_time - self.last_power_up_time
        
        if time_diff < 3:  # Collected within 3 seconds
            self.combo_multiplier = min(self.combo_multiplier * 1.5, 5.0)
        else:
            self.combo_multiplier = 1.0
            
        self.last_power_up_time = current_time
        return int(10 * self.combo_multiplier)

# Advanced obstacle patterns
class ObstaclePatterns:
    """Generate complex obstacle patterns"""
    
    @staticmethod
    def create_maze_section(obstacles, start_x, start_y, width, height):
        """Create a maze-like section"""
        for x in range(start_x, start_x + width, 2):
            for y in range(start_y, start_y + height, 2):
                if random.random() < 0.3:
                    obstacles.append(Obstacle(x, y, 1, 1, DARK_GRAY, 'maze'))
    
    @staticmethod
    def create_spiral_pattern(obstacles, center_x, center_y, radius):
        """Create a spiral pattern of obstacles"""
        angle = 0
        current_radius = 1
        
        while current_radius < radius:
            x = int(center_x + current_radius * math.cos(angle))
            y = int(center_y + current_radius * math.sin(angle))
            
            if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                obstacles.append(Obstacle(x, y, 1, 1, NEON_CYAN, 'spiral'))
            
            angle += 0.5
            current_radius += 0.1

# Game configuration and settings
class GameConfig:
    """Store game configuration and settings"""
    
    def __init__(self):
        self.difficulty = 'Normal'
        self.snake_color = NEON_GREEN
        self.food_color = NEON_PINK
        self.show_grid = True
        self.particle_effects = True
        self.screen_shake = True
        self.auto_pause_on_focus_loss = True
        
    def load_from_file(self, filename='snake_config.txt'):
        """Load configuration from file"""
        try:
            with open(filename, 'r') as f:
                # Simple key=value format
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        if hasattr(self, key):
                            setattr(self, key, value)
        except FileNotFoundError:
            pass
    
    def save_to_file(self, filename='snake_config.txt'):
        """Save configuration to file"""
        try:
            with open(filename, 'w') as f:
                f.write(f"difficulty={self.difficulty}\n")
                f.write(f"show_grid={self.show_grid}\n")
                f.write(f"particle_effects={self.particle_effects}\n")
                f.write(f"screen_shake={self.screen_shake}\n")
        except:
            pass

# Performance optimization for Raspberry Pi
class PerformanceManager:
    """Optimize performance for Raspberry Pi Zero 2W"""
    
    def __init__(self):
        self.target_fps = 60
        self.particle_limit = 50
        self.auto_reduce_effects = True
        self.frame_times = []
        
    def should_reduce_effects(self):
        """Check if effects should be reduced for performance"""
        if len(self.frame_times) < 10:
            return False
            
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return avg_frame_time > 1000 / self.target_fps
    
    def update_frame_time(self, frame_time):
        """Update frame time tracking"""
        self.frame_times.append(frame_time)
        if len(self.frame_times) > 30:
            self.frame_times.pop(0)

# Main execution
if __name__ == "__main__":
    try:
        # Initialize game
        print("Starting Retro Snake Game...")
        print("Optimized for Raspberry Pi Zero 2W")
        print("Controls: Arrow Keys = Move, Space = Pause/Start, Escape = Menu")
        
        game = SnakeGame()
        game.run()
        
    except KeyboardInterrupt:
        print("\nGame interrupted by user")
        pygame.quit()
        sys.exit()
    except Exception as e:
        print(f"Game error: {e}")
        pygame.quit()
        sys.exit(1)