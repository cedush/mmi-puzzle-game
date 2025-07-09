import pygame
import sys
import threading
import random

from voice_listener import voice_listener
from helpers import *
from sound_manager import play_music


pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Block Sorting Puzzle")
clock = pygame.time.Clock()

# Start background music
play_music("bg_music", loops=1)

# Generate grids
shuffled_colors = random.sample(COLOR_PALETTE, GRID_SIZE * GRID_SIZE)
goal_grid = [[shuffled_colors[row * GRID_SIZE + col] for col in range(GRID_SIZE)] for row in range(GRID_SIZE)]
puzzle_grid = shuffled_grid_from(goal_grid)

selected = None
hovered = None
turnNumber = 1
won = False
last_voice_command = ""

def handle_voice_command(command):
    global puzzle_grid, selected, hovered, turnNumber, last_voice_command

    last_voice_command = command

    if "swap" in command or "switch" in command:
        try:
            words = command.split()
            if "this" in command or "that" in command:
                swap_with_this(words, puzzle_grid, hovered)
            else:
                c1 = get_color_from_command(words[1])
                c2 = get_color_from_command(words[3])
                if c1 and c2:
                    swap_by_color(c1, c2)
        except Exception as e:
            print(f"Swap failed: {e}")
    elif "shuffle" in command:
        puzzle_grid[:] = shuffled_grid_from(goal_grid)
        selected = None

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
        global turnNumber
        turnNumber = swap_blocks(puzzle_grid, pos1, pos2, turnNumber)

def swap_with_this(words, grid, hovered):
    if hovered is None:
        print("[VOICE] No hovered block to refer to.")
        return

    color_name = next((word for word in words if word not in {"switch", "and", "swap", "this", "that"}), None)
    color_rgb = get_color_from_command(color_name)
    if not color_rgb:
        print(f"[VOICE] Unknown color: {color_name}")
        return

    target_pos = None
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if grid[r][c] == color_rgb:
                target_pos = (r, c)
                break
        if target_pos:
            break

    if target_pos and are_adjacent(hovered, target_pos):
        global turnNumber
        turnNumber = swap_blocks(grid, hovered, target_pos, turnNumber)

voice_thread = threading.Thread(target=voice_listener, args=(handle_voice_command,), daemon=True)
voice_thread.start()

while True:
    screen.fill(BACKGROUND_COLOR)
    draw_grid(screen, goal_grid)

    puzzle_top = GRID_SIZE * (BLOCK_SIZE + MARGIN) + MARGIN + GAP_BETWEEN_GRIDS
    puzzle_bottom = puzzle_top + GRID_SIZE * (BLOCK_SIZE + MARGIN)

    mouse_pos = pygame.mouse.get_pos()
    row = (mouse_pos[1] - puzzle_top) // (BLOCK_SIZE + MARGIN)
    col = mouse_pos[0] // (BLOCK_SIZE + MARGIN)

    hovered = (row, col) if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE else None
    draw_grid(screen, puzzle_grid, top_offset=puzzle_top, highlight=selected, hovered=hovered)

    if grids_match(goal_grid, puzzle_grid):
        if not won:
            play_music("win_music")
            won = True
        msg = f"Won in {turnNumber} turns!"
    else:
        msg = f"Now in turn {turnNumber}"

    # Win or turn message
    font = pygame.font.SysFont(None, 48)
    text = font.render(msg, True, (255, 255, 255))
    screen.blit(text, (WINDOW_WIDTH // 2 - text.get_width() // 2, 10))
    # Voice command message
    pygame.draw.rect(screen, (40, 40, 40), (0, puzzle_bottom + MARGIN, WINDOW_WIDTH - MARGIN, 30))
    voice_font = pygame.font.SysFont(None, 24)
    voice_text = voice_font.render(f"> {last_voice_command}", True, (200, 200, 200))
    screen.blit(voice_text, (MARGIN, puzzle_bottom + 2 * MARGIN))

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN and not won:
            clicked = get_cell_from_mouse(event.pos, puzzle_top)
            if clicked:
                if selected == clicked:
                    selected = None
                    select.play()
                elif selected and are_adjacent(selected, clicked):
                    turnNumber = swap_blocks(puzzle_grid, selected, clicked, turnNumber)
                    selected = None
                else:
                    selected = clicked
                    select.play()

    clock.tick(60)
