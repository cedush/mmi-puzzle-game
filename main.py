#from command_handling import handle_voice_command
from voice_listener import voice_listener
import pygame
import random
import sys
import threading

# Constants
GRID_SIZE = 3
BLOCK_SIZE = 100
MARGIN = 5
GAP_BETWEEN_GRIDS = 60
WINDOW_HEIGHT = (2 * GRID_SIZE * (BLOCK_SIZE + MARGIN)) + MARGIN + GAP_BETWEEN_GRIDS
WINDOW_WIDTH = GRID_SIZE * (BLOCK_SIZE + MARGIN) + MARGIN

hovered = None
selected = None



# Sounds
click = 0

# Colors
BACKGROUND_COLOR = (30, 30, 30)
HIGHLIGHT_COLOR = (255, 255, 255)

# 9 unique colors
COLOR_PALETTE = [
    (255, 0, 0),      # Red
    (0, 255, 0),      # Green
    (0, 0, 255),      # Blue
    (255, 255, 0),    # Yellow
    (255, 165, 0),    # Orange
    (128, 0, 128),    # Purple
    (0, 255, 255),    # Cyan
    (255, 192, 203),  # Pink
    (139, 69, 19),    # Brown
]

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Block Sorting Puzzle")
clock = pygame.time.Clock()

# Generate the goal grid (solution)
shuffled_colors = random.sample(COLOR_PALETTE, GRID_SIZE * GRID_SIZE)
goal_grid = [[shuffled_colors[row * GRID_SIZE + col] for col in range(GRID_SIZE)] for row in range(GRID_SIZE)]


# Load background music
pygame.mixer.music.load("background.mp3")
# Credit / Attribution
# Local Forecast – Elevator by Kevin MacLeod | https://incompetech.com/
# Music promoted by https://www.chosic.com/free-music/all/
# Creative Commons Creative Commons: By Attribution 3.0 License
# http://creativecommons.org/licenses/by/3.0/
# Also see txt file
pygame.mixer.music.play(loops=1)
 

# Make a deep copy and shuffle it for the puzzle
def shuffled_grid_from(goal):
    flat = sum(goal, [])
    while True:
        random.shuffle(flat)
        if flat != sum(goal, []):  # ensure it's not identical to goal
            break
    return [[flat[row * GRID_SIZE + col] for col in range(GRID_SIZE)] for row in range(GRID_SIZE)]

puzzle_grid = shuffled_grid_from(goal_grid)

def draw_grid(grid, top_offset=0, highlight=None, hovered=None):
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            x = col * (BLOCK_SIZE + MARGIN) + MARGIN
            y = row * (BLOCK_SIZE + MARGIN) + MARGIN + top_offset
            rect = pygame.Rect(x, y, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(screen, grid[row][col], rect)

            # Hover highlight (light border)
            if hovered == (row, col):
                pygame.draw.rect(screen, (200, 200, 200), rect, 3)

            # Selected highlight (strong border)
            if highlight == (row, col):
                pygame.draw.rect(screen, (255, 255, 255), rect, 5)

def get_cell_from_mouse(pos):
    x, y = pos
    puzzle_top = GRID_SIZE * (BLOCK_SIZE + MARGIN) + MARGIN + GAP_BETWEEN_GRIDS
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
        return False
    r1, c1 = a
    r2, c2 = b
    return abs(r1 - r2) + abs(c1 - c2) == 1

def swap_blocks(a, b):
    r1, c1 = a
    r2, c2 = b
    puzzle_grid[r1][c1], puzzle_grid[r2][c2] = puzzle_grid[r2][c2], puzzle_grid[r1][c1]

def grids_match(g1, g2):
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if g1[row][col] != g2[row][col]:
                return False
    return True

def swap_by_color(c1, c2):
    pos1 = pos2 = None
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            color = puzzle_grid[r][c]
            if color == c1 and not pos1:
                pos1 = (r, c)
            elif color == c2 and not pos2:
                pos2 = (r, c)
    if pos1 and pos2 and are_adjacent(pos1, pos2):
        swap_blocks(pos1, pos2)
        print(f"Swapped {c1} and {c2}")
    else:
        print("Blocks not adjacent or not found.")

def swap_with_this(words, grid, hovered):
    if hovered is None:
        print("[VOICE] No hovered block to refer to with 'this'.")
        return

    # Extract color name
    color_name = next((word for word in words if word not in {"switch", "and", "swap", "this", "that"} and word.isalpha()), None)

    if not color_name:
        print("[VOICE] No color found in command.")
        return

    # Convert color name to RGB
    color_rgb = get_color_from_command(color_name)
    if not color_rgb:
        print(f"[VOICE] Unknown color: {color_name}")
        return

    # Find position of the color block
    target_pos = None
    for r in range(len(grid)):
        for c in range(len(grid[r])):
            if grid[r][c] == color_rgb:
                target_pos = (r, c)
                break
        if target_pos:
            break

    if not target_pos:
        print(f"[VOICE] Could not find block with color {color_name}")
        return

    # Check adjacency
    if are_adjacent(hovered, target_pos):
        swap_blocks(hovered, target_pos)
        print(f"[VOICE] Swapped {hovered} and {target_pos}")
    else:
        print("[VOICE] Blocks not adjacent — can't swap.")

def handle_voice_command(command):
    global puzzle_grid, selected, hovered

    # Example command: "swap red and green"
    if "swap" in command or "switch" in command:
        try:
            words = command.split()

            if "this" in command or "that" in command:
                swap_with_this(words, puzzle_grid, hovered)

            else:
                c1 = get_color_from_command(words[1]) # TODO use more stable extraction of color
                c2 = get_color_from_command(words[3])
                swap_by_color(c1, c2)

        except Exception as e:
            print(f"Swap failed: {e}")

    elif "shuffle" in command:
        puzzle_grid = shuffled_grid_from(goal_grid)
        selected = None

    # TODO: "reset", "end", "new puzzle"

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
    return name_to_color[color_name]

# Game loop
voice_thread = threading.Thread(target=voice_listener, args=(handle_voice_command,), daemon=True)
voice_thread.start()

running = True
won = False

while running:
    screen.fill(BACKGROUND_COLOR)

    # Draw static goal grid at top
    draw_grid(goal_grid, top_offset=0)

    # Offset
    puzzle_top = GRID_SIZE * (BLOCK_SIZE + MARGIN) + MARGIN + GAP_BETWEEN_GRIDS

    # Update hovered cell
    mouse_pos = pygame.mouse.get_pos()
    x, y = mouse_pos
    row = (y - puzzle_top) // (BLOCK_SIZE + MARGIN)
    col = x // (BLOCK_SIZE + MARGIN)

    if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
        hovered = (row, col)
    else:
        hovered = None

    # Draw interactive puzzle grid
    draw_grid(
        puzzle_grid,
        top_offset=puzzle_top,
        highlight=selected,
        hovered=hovered
    )

    # Check win condition
    if grids_match(goal_grid, puzzle_grid):
        if not won:
            # Play victory music
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
                    
            pygame.mixer.music.load("won.mp3")
            # Credit / Attribution
            # Sparks by Chaël:
            # http://chael-music.com/ 
            # https://www.instagram.com/chaelmusic/ 
            # https://www.tiktok.com/@chael_music 
            # https://www.facebook.com/chaelmusicofficial
            # https://www.youtube.com/@chaelofficial
            # Music promoted by https://www.chosic.com/free-music/all/
 
            pygame.mixer.music.play(loops=1)
        won = True
        font = pygame.font.SysFont(None, 48)
        text = font.render("You solved it!", True, (255, 255, 255))
        screen.blit(text, (WINDOW_WIDTH // 2 - text.get_width() // 2, 10))


        
        

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            running = False
            break

        elif event.type == pygame.MOUSEBUTTONDOWN and not won:
            clicked = get_cell_from_mouse(event.pos)
            if clicked:
                if selected == clicked:
                    selected = None  # unselect
                elif selected and are_adjacent(selected, clicked):
                    swap_blocks(selected, clicked)
                    selected = None
                else:
                    selected = clicked

    clock.tick(60)

pygame.quit()
sys.exit()
