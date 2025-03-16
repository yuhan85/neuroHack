import pygame
import random
import time
import sys
import scipy
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import welch

import brainflow
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BrainFlowError, \
    BoardIds

from brainflow_stream import BrainFlowBoardSetup

WIDTH, HEIGHT = 800, 600

WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
YELLOW = (255, 255, 0)

player_size = 30
player_speed = 2
guard_size = 40
obstacle_size = 50
EEG_THRESHOLD = 60
eeg_max_value = 100

button_width, button_height = 150, 60

obstacles = [
    {"x": 110, "y": 50},
    {"x": 367, "y": 218},
    {"x": 390, "y": 450},
    {"x": 56, "y": 318},
    {"x": 490, "y": 150}
]

screen = None
font = None
background_tile_img = None
player_visible_img = None
player_hidden_img = None
box_img = None
door_img = None
key_img = None
guard_img = None

MENU_STATE = "main_menu"
countdown = 0

start_button_rect = None
start_game_button_rect = None
retry_button_rect = None
quit_button_rect = None

door_x, door_y = None, None

player_x, player_y = None, None
is_hidden = False
has_key = False
guards = []
key_x, key_y = None, None
current_eeg_value = 50
last_eeg_update = None

def compute_band_power(eeg_data, fs, bands):
    """
    Compute power in specified frequency bands using Welch's method.

    Parameters:
    
eeg_data: np.array of shape (n_chans, n_samples)
fs: Sampling frequency in Hz
bands: Dictionary of band names and their (low, high) frequency ranges

    Returns:
    
band_powers: np.array of shape (n_chans, len(bands)), containing power in each band"""
    nchans, n_samples = eeg_data.shape
    band_powers = np.zeros((8, len(bands)))

    # Compute PSD using Welch’s method
    f, psd = welch(eeg_data, fs=fs) #, nperseg=fs2)  # nperseg = window size (2 sec recommended)

    for i, (band_name, (low, high)) in enumerate(bands.items()):
        # Find indices corresponding to the band range
        idx_band = np.where((f >= low) & (f <= high))[0]
        # Integrate the PSD over the selected frequency range
        band_powers[:, i] = np.trapz(psd[:, idx_band], f[idx_band])

    return band_powers

def beta_alpha_ratio(band_powers, bands):
    # 获取 Beta 和 Alpha 频段在 band_powers 中的索引
    beta_idx = list(bands.keys()).index("Beta")
    alpha_idx = list(bands.keys()).index("Alpha")

    # 计算 Beta/Alpha 比值
    ratios = np.sum(band_powers[:, beta_idx], axis=-1) / np.sum(band_powers[:, alpha_idx], axis=-1)
    
    return ratios


def init_buttons() -> None:
    """
    Initialize the button rectangles using screen dimensions.
    
    This function calculates the positions of the start, retry, and quit
    buttons based on the global screen size. It mutates global variables to
    store the computed pygame.Rect objects, which are used for handling mouse
    click events in the UI.
    
    Returns
    -------
    None
        Mutates global state.
    """
    global start_button_rect, start_game_button_rect, retry_button_rect, quit_button_rect
    start_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2,
                                    HEIGHT // 2 - button_height // 2,
                                    button_width, button_height)
    start_game_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2,
                                         HEIGHT // 2 - button_height // 2,
                                         button_width, button_height)
    retry_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2,
                                    HEIGHT // 2 + 20,
                                    button_width, button_height)
    quit_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2,
                                   HEIGHT // 2 + 100,
                                   button_width, button_height)


def load_assets() -> None:
    """
    Load and scale image assets required by the game.
    
    This function loads images from file paths and scales them to the desired
    dimensions using pygame. The loaded images include player sprites, obstacles,
    and UI elements. This is essential for rendering the game graphics.
    
    Returns
    -------
    None
        Mutates global variables with loaded images.
    """
    global player_visible_img, player_hidden_img, box_img, door_img, key_img, \
        guard_img, background_tile_img
    player_visible_img = pygame.transform.scale(
        pygame.image.load("visable.png"), (50, 50))
    player_hidden_img = pygame.transform.scale(
        pygame.image.load("invisable.png"), (50, 50))
    box_img = pygame.transform.scale(pygame.image.load("box.png"), (50, 50))
    door_img = pygame.transform.scale(pygame.image.load("door.png"), (100, 100))
    key_img = pygame.transform.scale(pygame.image.load("key.png"), (50, 50))
    guard_img = pygame.transform.scale(pygame.image.load("guard.png"), (50, 50))
    background_tile_img = pygame.image.load("blue.png")


def init_game() -> None:
    """
    Initialize or reset all game variables and state.
    
    This function resets the player's position, EEG simulation values,
    guard positions, and key and door locations. It provides a clean slate for
    starting or restarting the game. It uses simple randomization for key
    placement and resets timers for simulated EEG updates.
    
    Returns
    -------
    None
        Mutates global game state.
    """
    global player_x, player_y, is_hidden, has_key, guards, key_x, key_y
    global current_eeg_value, last_eeg_update, door_x, door_y
    player_x, player_y = 100, 500
    is_hidden = False
    has_key = False
    guards = [
        {"x": 135, "y": 200, "speed": 1},
        {"x": 333, "y": 78, "speed": 1},
        {"x": 570, "y": 400, "speed": 1}
    ]
    key_x = random.randint(50, WIDTH - 50)
    key_y = random.randint(50, HEIGHT - 50)
    current_eeg_value = 50
    last_eeg_update = time.time()
    door_x, door_y = WIDTH - 100, HEIGHT // 2


def get_eeg_value() -> int:
    """
    Simulate an EEG reading by generating a random value.
    
    This function simulates the process of obtaining an EEG value using a
    random generator. It is a placeholder for real EEG data acquisition and
    returns an integer in the range [0, 100].
    
    Returns
    -------
    int
        A simulated EEG value.
    """
    return random.randint(0, 100)


def check_for_obstacle_collision(x: int, y: int, size: int) -> bool:
    """
    Check if an entity collides with any defined obstacles.
    
    This function iterates over the global list of obstacles and checks if the
    distance between the entity's position and the obstacle is less than the
    predefined obstacle size. This is used to avoid illegal movements.
    
    Parameters
    ----------
    x : int
        The x-coordinate of the entity.
    y : int
        The y-coordinate of the entity.
    size : int
        The size of the entity.
    
    Returns
    -------
    bool
        True if a collision is detected; otherwise, False.
    """
    for obstacle in obstacles:
        if abs(x - obstacle["x"]) < obstacle_size and abs(y - obstacle["y"]) < \
                obstacle_size:
            return True
    return False


def move_guards() -> None:
    """
    Update guard positions based on player visibility state.
    
    When the player is hidden, guards move in random directions. When the
    player is visible, guards use a simple chasing algorithm to approach the
    player's position. Guard positions are clamped to stay within screen bounds.
    
    Returns
    -------
    None
        Mutates global guard positions.
    """
    global guards, is_hidden, player_x, player_y
    for guard in guards:
        if is_hidden:
            direction = random.choice(["left", "right", "up", "down"])
            if direction == "left" and not check_for_obstacle_collision(
                    guard["x"] - guard["speed"], guard["y"], guard_size):
                guard["x"] -= guard["speed"]
            elif direction == "right" and not check_for_obstacle_collision(
                    guard["x"] + guard["speed"], guard["y"], guard_size):
                guard["x"] += guard["speed"]
            elif direction == "up" and not check_for_obstacle_collision(
                    guard["x"], guard["y"] - guard["speed"], guard_size):
                guard["y"] -= guard["speed"]
            elif direction == "down" and not check_for_obstacle_collision(
                    guard["x"], guard["y"] + guard["speed"], guard_size):
                guard["y"] += guard["speed"]
        else:
            if player_x > guard["x"] and not check_for_obstacle_collision(
                    guard["x"] + guard["speed"], guard["y"], guard_size):
                guard["x"] += guard["speed"]
            elif player_x < guard["x"] and not check_for_obstacle_collision(
                    guard["x"] - guard["speed"], guard["y"], guard_size):
                guard["x"] -= guard["speed"]
            if player_y > guard["y"] and not check_for_obstacle_collision(
                    guard["x"], guard["y"] + guard["speed"], guard_size):
                guard["y"] += guard["speed"]
            elif player_y < guard["y"] and not check_for_obstacle_collision(
                    guard["x"], guard["y"] - guard["speed"], guard_size):
                guard["y"] -= guard["speed"]
        guard["x"] = max(0, min(WIDTH - guard_size, guard["x"]))
        guard["y"] = max(0, min(HEIGHT - guard_size, guard["y"]))


def check_for_capture() -> bool:
    """
    Determine whether a guard has captured the player.
    
    This function calculates the Euclidean distance between each guard and
    the player. If the distance is less than a threshold determined by the
    player and guard sizes, it indicates that the player has been captured.
    
    Returns
    -------
    bool
        True if the player is caught by any guard; otherwise, False.
    """
    for guard in guards:
        distance = ((player_x - guard["x"]) ** 2 +
                    (player_y - guard["y"]) ** 2) ** 0.5
        if distance < player_size + guard_size // 2:
            return True
    return False


def draw_menu() -> None:
    """
    Render the main menu screen for the game.
    
    This function draws the game title, the start button, and usage
    instructions onto the screen. It serves as the entry point for the user
    interface before gameplay begins.
    
    Returns
    -------
    None
        Mutates the display state.
    """
    screen.fill(BLACK)
    title_text = font.render("EEG Escape Game", True, (150, 255, 255))
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2,
                             HEIGHT // 4))
    pygame.draw.rect(screen, (50, 50, 50), start_button_rect)
    pygame.draw.rect(screen, WHITE, start_button_rect, 2)
    text = font.render("Start", True, WHITE)
    screen.blit(text, (start_button_rect.x + (button_width - text.get_width()) // 2,
                       start_button_rect.y + (button_height - text.get_height()) // 2))
    instructions_text = font.render(
        "Use arrow keys to move. Stay calm to become invisible!", True, WHITE)
    screen.blit(instructions_text, (WIDTH // 2 - instructions_text.get_width() // 2,
                                    HEIGHT - 150))

def remove_dc_offset(data):
    return data[1:9, :] - np.mean(data[1:9, :], axis=1, keepdims=True)

def update_countdown(cyton_board) -> None:
    """
    Update and display the countdown timer before game start.
    
    This function renders a countdown message on the screen and delays
    execution to create a timer effect. Once the countdown reaches zero,
    it resets the game state and transitions the game mode.
    
    Returns
    -------
    None
        Mutates global countdown and game state.
    """
    raw_data_1250 = cyton_board.get_current_board_data(1250) # Get 1250 samples of data from the board.
    eeg_data = remove_dc_offset(raw_data_1250)
    fs = 250  # Example sampling rate
    bands = {"Delta": (0.5, 4), "Theta": (4, 8), "Alpha": (8, 13), "Beta": (13, 30), "Gamma": (30, 100)}
    band_power = compute_band_power(eeg_data, fs, bands)
    ratios = beta_alpha_ratio(band_power, bands)
    print(ratios)
    global countdown, MENU_STATE
    screen.fill(BLACK)
    countdown_text = font.render(f"Please calm down in {countdown} seconds",
                                 True, (150, 255, 255))
    screen.blit(countdown_text, (WIDTH // 2 - countdown_text.get_width() // 2,
                                 HEIGHT // 2 - 100))
    pygame.display.update()
    pygame.time.delay(1000)
    countdown -= 1
    if countdown == 0:
        MENU_STATE = "game"
        init_game()


def draw_game_over(message: str) -> None:
    """
    Render the game over or win screen overlay.
    
    This function displays an overlay with a message indicating whether the
    game was lost or won. It also renders interactive buttons for retrying or
    quitting, thereby providing options for the next action.
    
    Parameters
    ----------
    message : str
        The message to display (e.g., "Player caught!" or
        "Escape successful!").
    
    Returns
    -------
    None
        Mutates the display state.
    """
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))
    game_over_text = font.render(message, True, WHITE)
    screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2,
                                 HEIGHT // 3))
    pygame.draw.rect(screen, (50, 50, 50), retry_button_rect)
    pygame.draw.rect(screen, WHITE, retry_button_rect, 2)
    retry_text = font.render("Retry", True, WHITE)
    screen.blit(retry_text, (retry_button_rect.x +
                             (button_width - retry_text.get_width()) // 2,
                             retry_button_rect.y +
                             (button_height - retry_text.get_height()) // 2))
    pygame.draw.rect(screen, (50, 50, 50), quit_button_rect)
    pygame.draw.rect(screen, WHITE, quit_button_rect, 2)
    quit_text = font.render("Quit", True, WHITE)
    screen.blit(quit_text, (quit_button_rect.x +
                            (button_width - quit_text.get_width()) // 2,
                            quit_button_rect.y +
                            (button_height - quit_text.get_height()) // 2))


def handle_events() -> None:
    """
    Process user input and events across all game states.
    
    This function listens for events such as window closure and mouse clicks.
    It updates the global game state based on user interactions, for example,
    transitioning from the main menu to countdown or game over states.
    
    Returns
    -------
    None
        Mutates global game state based on event handling.
    """
    global MENU_STATE, countdown
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            if MENU_STATE == "main_menu":
                if start_button_rect.collidepoint(x, y):
                    MENU_STATE = "countdown"
                    countdown = 5
            elif MENU_STATE == "game_over":
                if retry_button_rect.collidepoint(x, y):
                    MENU_STATE = "countdown"
                    countdown = 5
                elif quit_button_rect.collidepoint(x, y):
                    pygame.quit()
                    sys.exit()


def run_game(cyton_board) -> None:
    """
    Execute per-frame game logic and render game elements.
    
    This function is called repeatedly during gameplay. It updates the EEG
    simulation, processes player movement, moves guards based on the player's
    state, and renders all visual components such as the background, player,
    obstacles, key, and door. It also checks for collision events to determine
    if the player has been caught or has escaped.
    
    Returns
    -------
    None
        Mutates global game state and display.
    """
    raw_data_250 = cyton_board.get_current_board_data(250) # Get 250 samples of data from the board.
    eeg_data = remove_dc_offset(raw_data_250)
    fs = 250  # Example sampling rate
    bands = {"Delta": (0.5, 4), "Theta": (4, 8), "Alpha": (8, 13), "Beta": (13, 30), "Gamma": (30, 100)}
    band_power = compute_band_power(eeg_data, fs, bands)
    ratios = beta_alpha_ratio(band_power, bands)
    print(ratios)
    global player_x, player_y, is_hidden, has_key, current_eeg_value, \
        last_eeg_update, MENU_STATE
    for tile_x in range(0, WIDTH, background_tile_img.get_width()):
        for tile_y in range(0, HEIGHT, background_tile_img.get_height()):
            screen.blit(background_tile_img, (tile_x, tile_y))
    if time.time() - last_eeg_update >= 1:
        current_eeg_value = get_eeg_value()
        last_eeg_update = time.time()
    is_hidden = current_eeg_value > EEG_THRESHOLD
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and not check_for_obstacle_collision(
            player_x - player_speed, player_y, player_size):
        player_x -= player_speed
    if keys[pygame.K_RIGHT] and not check_for_obstacle_collision(
            player_x + player_speed, player_y, player_size):
        player_x += player_speed
    if keys[pygame.K_UP] and not check_for_obstacle_collision(
            player_x, player_y - player_speed, player_size):
        player_y -= player_speed
    if keys[pygame.K_DOWN] and not check_for_obstacle_collision(
            player_x, player_y + player_speed, player_size):
        player_y += player_speed
    player_x = max(0, min(WIDTH - player_size, player_x))
    player_y = max(0, min(HEIGHT - player_size, player_y))
    screen.blit(door_img, (door_x, door_y))
    if not has_key:
        screen.blit(key_img, (key_x, key_y))
    if is_hidden:
        screen.blit(player_hidden_img, (player_x, player_y))
    else:
        screen.blit(player_visible_img, (player_x, player_y))
    for guard in guards:
        screen.blit(guard_img, (guard["x"], guard["y"]))
    for obstacle in obstacles:
        screen.blit(box_img, (obstacle["x"], obstacle["y"]))
    move_guards()
    if check_for_capture():
        MENU_STATE = "game_over"
        draw_game_over("Player caught!")
        return
    pygame.draw.rect(screen, GRAY, (50, HEIGHT - 50, 200, 20))
    eeg_bar_width = int((current_eeg_value / eeg_max_value) * 200)
    color = GREEN if is_hidden else RED
    pygame.draw.rect(screen, color, (50, HEIGHT - 50, eeg_bar_width, 20))
    threshold_x = 50 + int((EEG_THRESHOLD / eeg_max_value) * 200)
    pygame.draw.line(screen, BLACK, (threshold_x, HEIGHT - 55),
                     (threshold_x, HEIGHT - 30), 2)
    if not has_key and abs(player_x - key_x) < 20 and abs(player_y - key_y) < 20:
        has_key = True
    if has_key and abs(player_x - door_x) < 20 and abs(player_y - door_y) < 20:
        MENU_STATE = "game_over"
        draw_game_over("Escape successful!")
        return


def main() -> None:
    """
    Initialize the game and enter the main event loop.
    
    This function sets up the pygame environment, loads all required assets,
    initializes UI elements, and then continuously processes events and game
    logic in a loop. It also prepares the EEG board interface (if needed).
    
    Returns
    -------
    None
        Enters an infinite loop that mutates game and display state.
    """
    global screen, font, MENU_STATE
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("EEG Escape Game")
    load_assets()
    font = pygame.font.Font(None, 36)
    init_buttons()
    board_id = BoardIds.CYTON_BOARD.value
    for item1, item2 in BoardShim.get_board_descr(board_id).items():
        print(f"{item1}: {item2}")
    cyton_board = BrainFlowBoardSetup(
                                board_id = board_id,
                                name = 'Board_1', # Optional name for the board. This is useful if you have multiple boards connected and want to distinguish between them.
                                serial_port = None # If the serial port is not specified, it will try to auto-detect the board. If this fails, you will have to assign the correct serial port. See https://docs.openbci.com/GettingStarted/Boards/CytonGS/ 
                                ) 

    cyton_board.setup() # This will establish a connection to the board and start streaming data.
    board_info = cyton_board.get_board_info() # Retrieves the EEG channel and sampling rate of the board.
    print(f"Board info: {board_info}")

    board_srate = cyton_board.get_sampling_rate() # Retrieves the sampling rate of the board.
    print(f"Board sampling rate: {board_srate}")
    clock = pygame.time.Clock()
    while True:
        handle_events()
        if MENU_STATE == "main_menu":
            draw_menu()
        elif MENU_STATE == "countdown":
            print("Collect EEG data in 5s...")
            update_countdown(cyton_board)
        elif MENU_STATE == "game":
            run_game(cyton_board)
        pygame.display.update()
        clock.tick(60)


if __name__ == "__main__":
    main()

