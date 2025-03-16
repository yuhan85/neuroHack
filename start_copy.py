import pygame
import random
import time
import sys
import scipy
import numpy as np
import matplotlib.pyplot as plt

import brainflow
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BrainFlowError, BoardIds


# Import the custom module.
from brainflow_stream import BrainFlowBoardSetup



# Initialize pygame
pygame.init()


# Screen settings
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("EEG Escape Game")

# Load images
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

# Font
font = pygame.font.Font(None, 36)

# Menu variables
MENU_STATE = "main_menu"  # States: main_menu, countdown, game
countdown = 0
countdown_started = False

# Button dimensions and positions
button_width, button_height = 150, 60
start_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 - button_height // 2, button_width, button_height)
start_game_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 - button_height // 2, button_width, button_height)
retry_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 20, button_width, button_height)
quit_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 100, button_width, button_height)

# Game variables
def init_game():

    global player_x, player_y, is_hidden, has_key, guards, key_x, key_y, current_eeg_value, last_eeg_update
    
    # Player attributes
    player_x, player_y = 100, 500
    is_hidden = False  # Whether the player is invisible
    has_key = False  # Whether the player has obtained the key
    
    # Guard attributes
    guards = [
        {"x": 135, "y": 200, "speed": 1},
        {"x": 333, "y": 78, "speed": 1},
        {"x": 570, "y": 400, "speed": 1}
    ]
    
    # Key position
    key_x, key_y = random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50)
    
    # EEG variables
    current_eeg_value = 50  # Current EEG strength
    last_eeg_update = time.time()  # Time of the last EEG update

# Constants
player_size = 30
player_speed = 2
guard_size = 40
door_x, door_y = WIDTH - 100, HEIGHT // 2
obstacle_size = 50
EEG_THRESHOLD = 60  # Threshold, above which the player becomes invisible
eeg_max_value = 100  # Maximum EEG value

# Obstacles
obstacles = [
    {"x": 110, "y": 50},
    {"x": 367, "y": 218},
    {"x": 390, "y": 450},
    {"x": 56, "y": 318},
    {"x": 490, "y": 150}
]

# Initialize game variables
init_game()

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

def update_countdown():
    """Update the countdown display"""
    global countdown, MENU_STATE
    
    screen.fill(BLACK)
    countdown_text = font.render(f"Please calm down in {countdown} seconds", True, (150, 255, 255))
    screen.blit(countdown_text, (WIDTH // 2 - countdown_text.get_width() // 2, HEIGHT // 2 - 100))
    pygame.display.update()
    pygame.time.delay(1000)
    countdown -= 1
    
    if countdown == 0:
        MENU_STATE = "game"
        init_game()  # Reset game variables

def draw_menu():
    """Draw the main menu"""
    screen.fill(BLACK)
    
    # Title
    title_text = font.render("EEG Escape Game", True, (150, 255, 255))
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 4))
    
    # Start button
    pygame.draw.rect(screen, (50, 50, 50), start_button_rect)
    pygame.draw.rect(screen, WHITE, start_button_rect, 2)
    text = font.render("Start", True, WHITE)
    screen.blit(text, (start_button_rect.x + (button_width - text.get_width()) // 2,
                       start_button_rect.y + (button_height - text.get_height()) // 2))
    
    # Instructions
    instructions_text = font.render("Use arrow keys to move. Stay calm to become invisible!", True, WHITE)
    screen.blit(instructions_text, (WIDTH // 2 - instructions_text.get_width() // 2, HEIGHT - 150))

def draw_game_over(message):
    """Draw the game over screen"""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))
    
    # Game over message
    game_over_text = font.render(message, True, WHITE)
    screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 3))
    
    # Retry button
    pygame.draw.rect(screen, (50, 50, 50), retry_button_rect)
    pygame.draw.rect(screen, WHITE, retry_button_rect, 2)
    retry_text = font.render("Retry", True, WHITE)
    screen.blit(retry_text, (retry_button_rect.x + (button_width - retry_text.get_width()) // 2,
                         retry_button_rect.y + (button_height - retry_text.get_height()) // 2))
    
    # Quit button
    pygame.draw.rect(screen, (50, 50, 50), quit_button_rect)
    pygame.draw.rect(screen, WHITE, quit_button_rect, 2)
    quit_text = font.render("Quit", True, WHITE)
    screen.blit(quit_text, (quit_button_rect.x + (button_width - quit_text.get_width()) // 2,
                         quit_button_rect.y + (button_height - quit_text.get_height()) // 2))

def handle_events():
    """Handle user input and events"""
    global MENU_STATE, countdown_started, countdown
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            if MENU_STATE == "main_menu" and start_button_rect.collidepoint(x, y):
                MENU_STATE = "countdown"
                countdown = 5  # Set countdown time
            elif MENU_STATE == "game_over":
                if retry_button_rect.collidepoint(x, y):
                    MENU_STATE = "countdown"
                    countdown = 5
                elif quit_button_rect.collidepoint(x, y):
                    pygame.quit()
                    sys.exit()

def run_game():
    """Main game loop"""
    global player_x, player_y, is_hidden, has_key, current_eeg_value, last_eeg_update, MENU_STATE
    
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
    screen.blit(door_img, (door_x, door_y))

    # Draw the key (if not yet obtained)
    if not has_key:
        screen.blit(key_img, (key_x, key_y))

    # Draw the player
    if is_hidden:
        screen.blit(player_hidden_img, (player_x, player_y))
    else:
        screen.blit(player_visible_img, (player_x, player_y))

    # Draw the guards
    for guard in guards:
        screen.blit(guard_img, (guard["x"], guard["y"]))

    # Draw the obstacles
    for obstacle in obstacles:
        screen.blit(box_img, (obstacle["x"], obstacle["y"]))

    # Move the guards
    move_guards()

    # Check if caught
    if check_for_capture():
        MENU_STATE = "game_over"
        draw_game_over("Player caught!")
        return

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
    if has_key and abs(player_x - door_x) < 20 and abs(player_y - door_y) < 20:
        MENU_STATE = "game_over"
        draw_game_over("Escape successful!")
        return

    # Draw EEG status text
    #status_text = font.render("Status: " + ("Hidden" if is_hidden else "Visible"), True, WHITE)
    #screen.blit(status_text, (260, HEIGHT - 50))
    
    # Draw key status
    #key_status = font.render("Key: " + ("Found ✓" if has_key else "Not Found ✗"), True, WHITE)
    #screen.blit(key_status, (500, HEIGHT - 50))

# Main game loop
def main():
    """Main loop"""
    print("\n\n\n\n\nhello1\n\n\n\n\n")
    board_id = BoardIds.CYTON_BOARD.value # Set the board_id to match the Cyton board
    print("\n\n\n\n\nhello2\n\n\n\n\n")
    # Lets quickly take a look at the specifications of the Cyton board
    for item1, item2 in BoardShim.get_board_descr(board_id).items():
        print(f"{item1}: {item2}")
    print("\n\n\n\n\nhello3\n\n\n\n\n")
    global countdown, MENU_STATE
    print("\n\n\n\n\nhello4\n\n\n\n\n")
    clock = pygame.time.Clock()
    print("\n\n\n\n\nhello5\n\n\n\n\n")
    while True:
        handle_events()
        
        if MENU_STATE == "main_menu":
            draw_menu()
        elif MENU_STATE == "countdown":
            update_countdown()
        elif MENU_STATE == "game":
            print("\n\n\n\n\nhello6\n\n\n\n\n")
            run_game()
        # game_over state is handled in run_game()
        
        pygame.display.update()
        clock.tick(60)  # 60 FPS

if __name__ == "__main__":
    main()