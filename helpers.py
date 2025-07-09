import pygame
import random
from sound_manager import play_sound

# Constants
GRID_SIZE = 3
BLOCK_SIZE = 100
MARGIN = 5
GAP_BETWEEN_GRIDS = 20
VOICE_INPUT_BOX = 30
WINDOW_HEIGHT = (2 * GRID_SIZE * (BLOCK_SIZE + MARGIN)) + MARGIN + GAP_BETWEEN_GRIDS + VOICE_INPUT_BOX + 2 * MARGIN
WINDOW_WIDTH = GRID_SIZE * (BLOCK_SIZE + MARGIN) + MARGIN

# Colors
BACKGROUND_COLOR = (30, 30, 30)
HIGHLIGHT_COLOR = (255, 255, 255)
COLOR_PALETTE = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255),
    (255, 255, 0), (255, 165, 0), (128, 0, 128),
    (0, 255, 255), (255, 192, 203), (139, 69, 19),
]

# Sounds
pygame.mixer.init()
select = pygame.mixer.Sound("sounds/select.mp3")
swap = pygame.mixer.Sound("sounds/swap11labs.mp3")
fail = pygame.mixer.Sound("sounds/fail11labs.mp3")

def shuffled_grid_from(goal, grid_size=GRID_SIZE):
    flat = sum(goal, [])
    while True:
        random.shuffle(flat)
        if flat != sum(goal, []):
            break
    return [[flat[row * grid_size + col] for col in range(grid_size)] for row in range(grid_size)]

def draw_grid(screen, grid, top_offset=0, highlight=None, hovered=None):
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            x = col * (BLOCK_SIZE + MARGIN) + MARGIN
            y = row * (BLOCK_SIZE + MARGIN) + MARGIN + top_offset
            rect = pygame.Rect(x, y, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(screen, grid[row][col], rect)

            if hovered == (row, col):
                pygame.draw.rect(screen, (200, 200, 200), rect, 3)
            if highlight == (row, col):
                pygame.draw.rect(screen, (255, 255, 255), rect, 5)

def get_cell_from_mouse(pos, puzzle_top):
    x, y = pos
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            cell_x = MARGIN + col * (BLOCK_SIZE + MARGIN)
            cell_y = puzzle_top + MARGIN + row * (BLOCK_SIZE + MARGIN)
            rect = pygame.Rect(cell_x, cell_y, BLOCK_SIZE, BLOCK_SIZE)
            if rect.collidepoint(x, y):
                return (row, col)
    return None

def are_adjacent(a, b):
    if not a or not b:
        play_sound("fail")
        return False
    r1, c1 = a
    r2, c2 = b
    if abs(r1 - r2) + abs(c1 - c2) == 1:
        return True
    play_sound("fail")
    return False

def swap_blocks(grid, a, b, turn_counter):
    r1, c1 = a
    r2, c2 = b
    grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]
    play_sound("swap")
    return turn_counter + 1

def grids_match(g1, g2):
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if g1[row][col] != g2[row][col]:
                return False
    return True

def get_color_from_command(color_name):
    name_to_color = {
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "yellow": (255, 255, 0),
        "orange": (255, 165, 0),
        "purple": (128, 0, 128),
        "cyan": (0, 255, 255),
        "pink": (255, 192, 203),
        "brown": (139, 69, 19),
    }
    return name_to_color.get(color_name.lower())
