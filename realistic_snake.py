#!/usr/bin/env python3
"""
HYPER-REALISTIC Snake Simulation
Features: Advanced physics, breathing, hunting behavior, ecosystem simulation
"""

import pygame
import random
import math
import sys
import time
import noise

pygame.init()

# Constants
W, H = 1000, 800
TERRAIN_SCALE = 0.02

# Ultra-realistic colors
GRASS_BASE = (34, 59, 22)
DIRT = (71, 49, 33)
WATER = (28, 107, 160)
SNAKE_COLORS = [(15, 40, 15), (25, 60, 25), (40, 80, 40), (60, 100, 60)]
PREY_COLORS = [(139, 69, 19), (160, 82, 45), (205, 133, 63)]

class TerrainTile:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.height = noise.pnoise2(x * TERRAIN_SCALE, y * TERRAIN_SCALE) * 100
        self.moisture = noise.pnoise2(x * TERRAIN_SCALE * 0.5, y * TERRAIN_SCALE * 0.5) * 50 + 50
        self.vegetation = max(0, self.moisture - abs(self.height) * 0.3)
        self.color = self.calculate_color()
        
    def calculate_color(self):
        if self.height < -20: return WATER
        elif self.vegetation > 40: 
            green_intensity = min(255, int(50 + self.vegetation * 2))
            return (10, green_intensity, 20)
        else: 
            return (int(DIRT[0] + self.height * 0.2), int(DIRT[1] + self.height * 0.1), DIRT[2])

class SnakeSegment:
    def __init__(self, x, y, prev=None, index=0):
        self.x, self.y = float(x), float(y)
        self.old_x, self.old_y = x, y
        self.prev = prev
        self.index = index
        self.angle = 0
        self.target_angle = 0
        self.width = max(3, 25 - index * 1.2)
        self.breathing = random.random() * 6.28
        self.muscle_tension = 0
        self.scale_pattern = [random.random() for _ in range(8)]
        
    def update(self, dt):
        self.old_x, self.old_y = self.x, self.y
        
        if self.prev:
            # Advanced following with spring physics
            target_dist = self.width * 0.8
            dx = self.prev.x - self.x
            dy = self.prev.y - self.y
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist > 0:
                # Spring force
                force = (dist - target_dist) * 0.15
                self.x += (dx / dist) * force * dt
                self.y += (dy / dist) * force * dt
                
                # Update angle for realistic bending
                self.target_angle = math.atan2(dy, dx)
                angle_diff = self.target_angle - self.angle
                while angle_diff > math.pi: angle_diff -= 2 * math.pi
                while angle_diff < -math.pi: angle_diff += 2 * math.pi
                self.angle += angle_diff * 0.1
        
        # Breathing animation
        self.breathing += 2 * dt
        self.muscle_tension = 0.5 + 0.3 * math.sin(self.breathing)
        
    def draw(self, screen, camera_x, camera_y):
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        if -50 < screen_x < W + 50 and -50 < screen_y < H + 50:
            # Dynamic width with breathing
            current_width = self.width * self.muscle_tension
            
            # Multi-layer rendering for realism
            for layer in range(int(current_width // 2)):
                alpha = 255 - layer * 15
                layer_width = current_width - layer * 2
                
                # Scale coloration
                color_index = (self.index + layer) % len(SNAKE_COLORS)
                base_color = SNAKE_COLORS[color_index]
                
                # Add scale texture
                scale_offset = int(self.scale_pattern[layer % 8] * 30)
                color = (min(255, base_color[0] + scale_offset), 
                        min(255, base_color[1] + scale_offset), 
                        min(255, base_color[2] + scale_offset // 2))
                
                # Shadow
                pygame.draw.circle(screen, (0, 0, 0, 30), 
                                 (int(screen_x + 2), int(screen_y + 2)), int(layer_width))
                
                # Main body
                pygame.draw.circle(screen, color, 
                                 (int(screen_x), int(screen_y)), int(layer_width))
            
            # Detailed scales for head
            if self.index == 0:
                for i in range(6):
                    scale_x = screen_x + math.cos(i) * current_width * 0.3
                    scale_y = screen_y + math.sin(i) * current_width * 0.3
                    pygame.draw.circle(screen, (5, 20, 5), (int(scale_x), int(scale_y)), 2)
                
                # Eyes
                eye_offset = current_width * 0.6
                eye1_x = screen_x + math.cos(self.angle + 0.3) * eye_offset
                eye1_y = screen_y + math.sin(self.angle + 0.3) * eye_offset
                eye2_x = screen_x + math.cos(self.angle - 0.3) * eye_offset
                eye2_y = screen_y + math.sin(self.angle - 0.3) * eye_offset
                
                pygame.draw.circle(screen, (255, 255, 0), (int(eye1_x), int(eye1_y)), 3)
                pygame.draw.circle(screen, (255, 255, 0), (int(eye2_x), int(eye2_y)), 3)
                pygame.draw.circle(screen, (0, 0, 0), (int(eye1_x), int(eye1_y)), 1)
                pygame.draw.circle(screen, (0, 0, 0), (int(eye2_x), int(eye2_y)), 1)

class Prey:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vx = self.vy = 0
        self.fear_level = 0
        self.size = random.randint(8, 15)
        self.color = random.choice(PREY_COLORS)
        self.alive = True
        self.last_move = time.time()
        self.energy = 100
        
    def update(self, snake_head, dt):
        if not self.alive: return
        
        # Fear response to snake
        dist_to_snake = math.sqrt((self.x - snake_head.x)**2 + (self.y - snake_head.y)**2)
        if dist_to_snake < 150:
            self.fear_level = min(100, 100 - dist_to_snake)
            # Flee from snake
            flee_x = (self.x - snake_head.x) / dist_to_snake
            flee_y = (self.y - snake_head.y) / dist_to_snake
            self.vx += flee_x * self.fear_level * 0.01
            self.vy += flee_y * self.fear_level * 0.01
        else:
            self.fear_level *= 0.95
            
        # Random wandering when calm
        if self.fear_level < 20 and time.time() - self.last_move > random.uniform(0.5, 2.0):
            self.vx += random.uniform(-0.5, 0.5)
            self.vy += random.uniform(-0.5, 0.5)
            self.last_move = time.time()
            
        # Apply movement with friction
        self.vx *= 0.9
        self.vy *= 0.9
        max_speed = 2 + self.fear_level * 0.05
        speed = math.sqrt(self.vx**2 + self.vy**2)
        if speed > max_speed:
            self.vx = (self.vx / speed) * max_speed
            self.vy = (self.vy / speed) * max_speed
            
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Energy depletion
        self.energy -= dt * (1 + self.fear_level * 0.1)
        if self.energy <= 0:
            self.alive = False
            
    def draw(self, screen, camera_x, camera_y):
        if not self.alive: return
        
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        
        if -20 < screen_x < W + 20 and -20 < screen_y < H + 20:
            # Fear indicator
            if self.fear_level > 10:
                fear_color = (int(255 * self.fear_level / 100), 0, 0)
                pygame.draw.circle(screen, fear_color, 
                                 (int(screen_x), int(screen_y)), self.size + 3, 2)
            
            # Body
            pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), self.size)
            pygame.draw.circle(screen, (min(255, self.color[0] + 40), 
                                      min(255, self.color[1] + 40), 
                                      min(255, self.color[2] + 40)), 
                             (int(screen_x - 2), int(screen_y - 2)), self.size // 2)

class RealisticEcosystem:
    def __init__(self):
        self.screen = pygame.display.set_mode((W, H))
        pygame.display.set_caption("Hyper-Realistic Snake Ecosystem")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        
        # Generate terrain
        self.terrain = {}
        for x in range(-100, 201, 10):
            for y in range(-100, 201, 10):
                self.terrain[(x, y)] = TerrainTile(x, y)
        
        self.reset()
        
    def reset(self):
        # Create realistic snake
        start_x, start_y = 0, 0
        self.snake = []
        for i in range(15):
            segment = SnakeSegment(start_x - i * 5, start_y, 
                                 self.snake[-1] if self.snake else None, i)
            self.snake.append(segment)
            
        self.head = self.snake[0]
        self.direction = 0  # Radians
        self.speed = 0
        self.max_speed = 3
        self.hunger = 0
        self.energy = 100
        
        # Ecosystem
        self.prey = []
        for _ in range(20):
            self.spawn_prey()
            
        self.camera_x = self.camera_y = 0
        self.time = 0
        self.score = 0
        
    def spawn_prey(self):
        angle = random.random() * 6.28
        distance = random.uniform(100, 300)
        x = self.head.x + math.cos(angle) * distance
        y = self.head.y + math.sin(angle) * distance
        self.prey.append(Prey(x, y))
        
    def handle_input(self):
        keys = pygame.key.get_pressed()
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        # Realistic snake control - follow mouse with momentum
        world_mouse_x = mouse_x + self.camera_x
        world_mouse_y = mouse_y + self.camera_y
        
        target_angle = math.atan2(world_mouse_y - self.head.y, world_mouse_x - self.head.x)
        angle_diff = target_angle - self.direction
        while angle_diff > math.pi: angle_diff -= 2 * math.pi
        while angle_diff < -math.pi: angle_diff += 2 * math.pi
        
        # Realistic turning speed
        max_turn = 0.08 if self.speed > 1 else 0.15
        self.direction += max(-max_turn, min(max_turn, angle_diff))
        
        # Speed control
        if keys[pygame.K_SPACE]:
            self.speed = min(self.max_speed, self.speed + 0.1)
            self.energy -= 0.5
        else:
            self.speed *= 0.95
            
    def update(self):
        dt = self.clock.get_time() / 16.67  # Normalize to 60fps
        self.time += dt
        
        # Update snake head
        self.head.x += math.cos(self.direction) * self.speed * dt
        self.head.y += math.sin(self.direction) * self.speed * dt
        self.head.angle = self.direction
        
        # Update all segments
        for segment in self.snake:
            segment.update(dt)
            
        # Update prey
        for prey in self.prey[:]:
            prey.update(self.head, dt)
            if not prey.alive:
                self.prey.remove(prey)
                
        # Hunting mechanics
        for prey in self.prey[:]:
            if prey.alive:
                dist = math.sqrt((self.head.x - prey.x)**2 + (self.head.y - prey.y)**2)
                if dist < self.head.width:
                    prey.alive = False
                    self.prey.remove(prey)
                    self.grow()
                    self.score += 10
                    self.energy = min(100, self.energy + 30)
                    self.hunger = max(0, self.hunger - 20)
                    
        # Spawn new prey
        if len(self.prey) < 15:
            self.spawn_prey()
            
        # Metabolism
        self.hunger += 0.1 * dt
        self.energy -= 0.05 * dt
        if self.hunger > 100 or self.energy <= 0:
            self.reset()
            
        # Camera follows snake
        self.camera_x += (self.head.x - W//2 - self.camera_x) * 0.05
        self.camera_y += (self.head.y - H//2 - self.camera_y) * 0.05
        
    def grow(self):
        tail = self.snake[-1]
        new_segment = SnakeSegment(tail.x - 10, tail.y - 10, tail, len(self.snake))
        self.snake.append(new_segment)
        
    def draw_terrain(self):
        # Draw visible terrain
        start_x = int((self.camera_x - 50) // 10) * 10
        start_y = int((self.camera_y - 50) // 10) * 10
        
        for x in range(start_x, start_x + W + 100, 10):
            for y in range(start_y, start_y + H + 100, 10):
                if (x, y) in self.terrain:
                    tile = self.terrain[(x, y)]
                    screen_x = x - self.camera_x
                    screen_y = y - self.camera_y
                    
                    if -20 < screen_x < W + 20 and -20 < screen_y < H + 20:
                        pygame.draw.rect(self.screen, tile.color, 
                                       (screen_x, screen_y, 10, 10))
                        
                        # Add texture details
                        if tile.vegetation > 30:
                            for _ in range(2):
                                grass_x = screen_x + random.randint(0, 8)
                                grass_y = screen_y + random.randint(0, 8)
                                pygame.draw.circle(self.screen, (20, 80, 20), 
                                                 (grass_x, grass_y), 1)
    
    def draw_ui(self):
        # Realistic HUD
        energy_bar = pygame.Rect(10, 10, 200, 20)
        hunger_bar = pygame.Rect(10, 40, 200, 20)
        
        pygame.draw.rect(self.screen, (50, 50, 50), energy_bar)
        pygame.draw.rect(self.screen, (0, 100, 0), 
                        (10, 10, self.energy * 2, 20))
        
        pygame.draw.rect(self.screen, (50, 50, 50), hunger_bar)
        pygame.draw.rect(self.screen, (100, 50, 0), 
                        (10, 40, min(200, self.hunger * 2), 20))
        
        # Labels
        energy_text = self.font.render(f"Energy: {int(self.energy)}", True, (255, 255, 255))
        hunger_text = self.font.render(f"Hunger: {int(self.hunger)}", True, (255, 255, 255))
        score_text = self.font.render(f"Prey Caught: {self.score // 10}", True, (255, 255, 255))
        
        self.screen.blit(energy_text, (220, 10))
        self.screen.blit(hunger_text, (220, 40))
        self.screen.blit(score_text, (10, 70))
        
        # Instructions
        inst = self.font.render("Move mouse to guide snake, hold SPACE to accelerate", True, (200, 200, 200))
        self.screen.blit(inst, (10, H - 30))
        
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    
            self.handle_input()
            self.update()
            
            self.screen.fill((0, 0, 0))
            self.draw_terrain()
            
            # Draw prey
            for prey in self.prey:
                prey.draw(self.screen, self.camera_x, self.camera_y)
                
            # Draw snake
            for segment in reversed(self.snake):
                segment.draw(self.screen, self.camera_x, self.camera_y)
                
            self.draw_ui()
            
            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    try:
        game = RealisticEcosystem()
        game.run()
    except ImportError:
        print("Installing noise library for terrain generation...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "noise"])
        game = RealisticEcosystem()
        game.run()