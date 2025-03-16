import pygame
import random
import time

# Initialize pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("EEG Escape Game")

player_visible_img = pygame.transform.scale(pygame.image.load("visable.png"), (50, 50))
player_hidden_img = pygame.transform.scale(pygame.image.load("invisable.png"), (50, 50))  
box_img = pygame.transform.scale(pygame.image.load("box.png"), (50, 50)) 
door_img = pygame.transform.scale(pygame.image.load("door.png"), (100, 100))
key_img = pygame.transform.scale(pygame.image.load("key.png"), (50, 50))
guard_img = pygame.transform.scale(pygame.image.load("guard.png"), (50, 50))
background_tile_img = pygame.image.load("blue.png")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
YELLOW = (255, 255, 0)

# Player attributes
player_size = 30
player_x, player_y = 100, 500
player_speed = 4
is_hidden = False  # Whether the player is invisible
has_key = False  # Whether the player has obtained the key

# Guard attributes
guard_size = 40
guards = [
    {"x": 135, "y": 200, "speed": 2},
    {"x": 333, "y": 78, "speed": 2},
    {"x": 570, "y": 400, "speed": 2}
]

# Door and key
key_x, key_y = random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50)
door_x, door_y = WIDTH - 100, HEIGHT // 2

# Obstacle attributes
obstacle_size = 50
obstacles = [
    {"x": 110, "y": 50},
    {"x": 367, "y": 218},
    {"x": 390, "y": 450},
    {"x": 56, "y": 318},
    {"x": 490, "y": 150}
]

# EEG variables
EEG_THRESHOLD = 60  # Threshold, above which the player becomes invisible
current_eeg_value = 50  # Current EEG strength
eeg_max_value = 100  # Maximum EEG value
last_eeg_update = time.time()  # Time of the last EEG update

# EEG reading (simulated using random here)
def get_eeg_value():
    return random.randint(0, 100)

# Guard movement logic
def move_guards():
    for guard in guards:
        if is_hidden:
            # Random movement (guards wander around when invisible)
            direction = random.choice(["left", "right", "up", "down"])
            if direction == "left" and not check_for_obstacle_collision(guard["x"] - guard["speed"], guard["y"], guard_size):
                guard["x"] -= guard["speed"]
            elif direction == "right" and not check_for_obstacle_collision(guard["x"] + guard["speed"], guard["y"], guard_size):
                guard["x"] += guard["speed"]
            elif direction == "up" and not check_for_obstacle_collision(guard["x"], guard["y"] - guard["speed"], guard_size):
                guard["y"] -= guard["speed"]
            elif direction == "down" and not check_for_obstacle_collision(guard["x"], guard["y"] + guard["speed"], guard_size):
                guard["y"] += guard["speed"]
        else:
            # Track the player (guards chase the player when visible)
            if player_x > guard["x"] and not check_for_obstacle_collision(guard["x"] + guard["speed"], guard["y"], guard_size):
                guard["x"] += guard["speed"]
            elif player_x < guard["x"] and not check_for_obstacle_collision(guard["x"] - guard["speed"], guard["y"], guard_size):
                guard["x"] -= guard["speed"]
            if player_y > guard["y"] and not check_for_obstacle_collision(guard["x"], guard["y"] + guard["speed"], guard_size):
                guard["y"] += guard["speed"]
            elif player_y < guard["y"] and not check_for_obstacle_collision(guard["x"], guard["y"] - guard["speed"], guard_size):
                guard["y"] -= guard["speed"]

        # Limit guard range
        guard["x"] = max(0, min(WIDTH - guard_size, guard["x"]))
        guard["y"] = max(0, min(HEIGHT - guard_size, guard["y"]))

# Check if the player is caught
def check_for_capture():
    for guard in guards:
        # Calculate the distance between the player and the guard
        distance = ((player_x - guard["x"])**2 + (player_y - guard["y"])**2) ** 0.5
        if distance < player_size + guard_size // 2:  # If collision, catch the player
            return True
    return False

# Check for collisions with obstacles
def check_for_obstacle_collision(x, y, size):
    for obstacle in obstacles:
        if abs(x - obstacle["x"]) < obstacle_size and abs(y - obstacle["y"]) < obstacle_size:
            return True
    return False

def show_message_box(message):
    """显示提示框"""
    root = pygame.display.get_wm_info()['window']
    import ctypes
    ctypes.windll.user32.MessageBoxW(root, message, "Game Over", 0x40 | 0x1)

# Main loop
running = True
while running:
    # Fill the screen with the background tile
    for x in range(0, WIDTH, background_tile_img.get_width()):
        for y in range(0, HEIGHT, background_tile_img.get_height()):
            screen.blit(background_tile_img, (x, y))

    # Update EEG data every second
    if time.time() - last_eeg_update >= 1:  # If one second has passed
        current_eeg_value = get_eeg_value()
        last_eeg_update = time.time()  # Record the new update time

    # State switching logic
    is_hidden = current_eeg_value > EEG_THRESHOLD  # EEG above threshold, become invisible

    # Player movement control
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and not check_for_obstacle_collision(player_x - player_speed, player_y, player_size):
        player_x -= player_speed
    if keys[pygame.K_RIGHT] and not check_for_obstacle_collision(player_x + player_speed, player_y, player_size):
        player_x += player_speed
    if keys[pygame.K_UP] and not check_for_obstacle_collision(player_x, player_y - player_speed, player_size):
        player_y -= player_speed
    if keys[pygame.K_DOWN] and not check_for_obstacle_collision(player_x, player_y + player_speed, player_size):
        player_y += player_speed

    # Limit player range
    player_x = max(0, min(WIDTH - player_size, player_x))
    player_y = max(0, min(HEIGHT - player_size, player_y))

    # Draw the door
    screen.blit(door_img, (door_x, door_y, 40, 60))

    # Draw the key (if not yet obtained)
    if not has_key:
        screen.blit(key_img, (key_x, key_y, 40, 60))

    # Draw the player (turn blue when invisible)
    # player_color = BLUE if is_hidden else RED
    # pygame.draw.rect(screen, player_color, (player_x, player_y, player_size, player_size))
    if is_hidden:
        screen.blit(player_hidden_img, (player_x, player_y))
    else:
        screen.blit(player_visible_img, (player_x, player_y))

    # Draw the guards
    for guard in guards:
        #pygame.draw.rect(screen, BLACK, (guard["x"], guard["y"], guard_size, guard_size))
        screen.blit(guard_img, (guard["x"], guard["y"], guard_size, guard_size))

    # Draw the obstacles
    for obstacle in obstacles:
        screen.blit(box_img, (obstacle["x"], obstacle["y"]))

    # Move the guards
    move_guards()

    # Check if caught
    if check_for_capture():
        show_message_box("💀 Player caught!")
        running = False  # Exit the game

    # Draw EEG progress bar background
    pygame.draw.rect(screen, GRAY, (50, HEIGHT - 50, 200, 20))  # EEG background bar

    # Draw EEG progress
    eeg_bar_width = int((current_eeg_value / eeg_max_value) * 200)
    pygame.draw.rect(screen, GREEN if is_hidden else RED, (50, HEIGHT - 50, eeg_bar_width, 20))

    # Draw threshold line
    threshold_x = 50 + int((EEG_THRESHOLD / eeg_max_value) * 200)
    pygame.draw.line(screen, BLACK, (threshold_x, HEIGHT - 55), (threshold_x, HEIGHT - 30), 2)

    # Check if the key is picked up
    if not has_key and abs(player_x - key_x) < 20 and abs(player_y - key_y) < 20:
        has_key = True  # Pick up the key

    # Check if the player has won
    if has_key and abs(player_x - door_x) < 5 and abs(player_y - door_y) < 5:
        show_message_box("🎉 Escape successful!")
        running = False  # Exit the game

    # Event listening
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()
    pygame.time.delay(100)  # Control frame rate

pygame.quit()