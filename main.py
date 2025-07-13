import pygame
import sys
import threading
import random
from enum import Enum

from voice_listener import voice_listener
from helpers import *
from sound_manager import play_music, stop_music, play_sound

pygame.init()


# Window setup
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("MMI Puzzle Game")
clock = pygame.time.Clock()


# Game‑states
class GameState(Enum):
    MENU = 0
    PLAYING = 1
    GAME_OVER = 2


# Runtime globals (is reset between rounds)
state: GameState = GameState.MENU
is_processing_action = False  # lock to prevent concurrent actions

goal_grid = []  # immutable reference grid (top)
puzzle_grid = []  # user‑manipulated grid (bottom)
selected = None  # currently selected cell in puzzle grid
hovered = None  # cell currently under mouse cursor
turn_number = 1
won = False
last_voice_command = ""
is_muted = False  # new state for mute button


# Helpers
def init_round() -> None:
    """Create a fresh goal/puzzle grid and reset round‑specific vars."""
    global goal_grid, puzzle_grid, selected, hovered, turn_number, won, last_voice_command, is_processing_action, is_muted

    shuffled_colors = random.sample(COLOR_PALETTE, GRID_SIZE * GRID_SIZE)
    goal_grid = [
        [shuffled_colors[r * GRID_SIZE + c] for c in range(GRID_SIZE)]
        for r in range(GRID_SIZE)
    ]
    puzzle_grid = shuffled_grid_from(goal_grid)

    selected = None
    hovered = None
    turn_number = 1
    won = False
    last_voice_command = ""
    is_processing_action = False
    is_muted = False # reset mute state on new round


def draw_menu() -> pygame.Rect:
    """Render title and a start button; returns the button rect."""
    screen.fill(BACKGROUND_COLOR)

    # Title
    title_font = pygame.font.SysFont(None, 64)
    title_surf = title_font.render("MMI Puzzle Game", True, (255, 255, 255))
    title_rect = title_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
    screen.blit(title_surf, title_rect)

    # Start button
    btn_font = pygame.font.SysFont(None, 48)
    label_surf = btn_font.render("Start", True, (0, 0, 0))
    padding = 20
    btn_rect = label_surf.get_rect()
    btn_rect.inflate_ip(padding * 2, padding * 2)
    btn_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

    pygame.draw.rect(screen, (200, 200, 200), btn_rect, border_radius=10)
    screen.blit(label_surf, label_surf.get_rect(center=btn_rect.center))

    return btn_rect


def draw_game_hud() -> None:
    """Information footer under the puzzle grid."""
    # Turn counter / win message
    font = pygame.font.SysFont(None, 48)
    msg = f"Won in {turn_number} turns!" if won else f"Turn {turn_number}"
    msg_surface = font.render(msg, True, (255, 255, 255))
    screen.blit(msg_surface, msg_surface.get_rect(center=(
        GRID_OFFSET_X + (GRID_SIZE * BLOCK_SIZE) // 2 + 2 * MARGIN,
        GRID_SIZE * BLOCK_SIZE + GAP_BETWEEN_GRIDS + MARGIN))
    )

    # Voice command line
    puzzle_bottom = (GRID_SIZE * 2) * (BLOCK_SIZE + MARGIN) + GAP_BETWEEN_GRIDS
    pygame.draw.rect(
        screen, (40, 40, 40), (0, puzzle_bottom + MARGIN, WINDOW_WIDTH, 30)
    )
    v_font = pygame.font.SysFont(None, 24)
    screen.blit(
        v_font.render(f"> {last_voice_command}", True, (200, 200, 200)),
        (MARGIN, puzzle_bottom + 2 * MARGIN),
    )

    # Color legend (left)
    legend_font = pygame.font.SysFont(None, 24)
    x0, y0 = 10, 100
    step, r = 30, 8
    for i, (name, col) in enumerate(name_to_color.items()):
        y = y0 + i * step
        pygame.draw.circle(screen, col, (x0 + r, y + r), r)
        screen.blit(
            legend_font.render(name.capitalize(), True, (220, 220, 220)),
            (x0 + r * 2 + 8, y),
        )


def draw_game_over() -> pygame.Rect:
    """Draw game-over screen and return the button rect."""
    screen.fill(BACKGROUND_COLOR)

    # Headline
    h_font = pygame.font.SysFont(None, 60)
    h_surf = h_font.render(f"Won in {turn_number} moves!", True, (255, 255, 255))
    h_rect = h_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
    screen.blit(h_surf, h_rect)

    # Back‑to‑menu button
    b_font = pygame.font.SysFont(None, 48)
    label = b_font.render("Back to Menu", True, (0, 0, 0))
    padding = 20
    btn_rect = label.get_rect()
    btn_rect.inflate_ip(padding * 2, padding * 2)
    btn_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
    pygame.draw.rect(screen, (200, 200, 200), btn_rect, border_radius=10)
    screen.blit(label, label.get_rect(center=btn_rect.center))

    return btn_rect

# new function to draw the mute button
def draw_mute_button(screen, muted) -> pygame.Rect:
    """Draws the mute button in the top right and returns its rect."""
    text = "Unmute" if muted else "Mute"
    font = pygame.font.SysFont(None, 32)
    label_surf = font.render(text, True, (0, 0, 0))
    
    padding = 10
    btn_rect = label_surf.get_rect()
    btn_rect.inflate_ip(padding * 2, padding * 2)
    btn_rect.topright = (WINDOW_WIDTH - MARGIN, MARGIN) # position in top-right

    pygame.draw.rect(screen, (200, 200, 200), btn_rect, border_radius=8)
    screen.blit(label_surf, label_surf.get_rect(center=btn_rect.center))
    
    return btn_rect

# new function to handle the mute logic
def toggle_mute() -> None:
    """Toggles the mute state and pauses/unpauses music."""
    global is_muted
    is_muted = not is_muted
    if is_muted:
        pygame.mixer.music.pause()
    else:
        pygame.mixer.music.unpause()
    play_sound("select")


def start_round() -> None:
    global state
    stop_music()
    init_round()
    play_music("bg_music", loops=-1)
    state = GameState.PLAYING


def return_to_menu() -> None:
    global state
    stop_music()
    state = GameState.MENU


# Voice‑command
def handle_voice_command(command: str) -> None:
    global puzzle_grid, selected, hovered, turn_number, last_voice_command, is_processing_action
    
    # fission solution: if a mouse selection is active, ignore voice commands
    if selected is not None:
        last_voice_command = "Finish mouse action before using voice."
        return

    if state != GameState.PLAYING or is_processing_action:
        return

    last_voice_command = command

    try:
        is_processing_action = True  # lock action while processing command
        if any(k in command for k in ("swap", "switch")):
            words = command.split()
            if any(w in command for w in ("this", "that")):
                swap_with_this(words, puzzle_grid, hovered)
            else:
                # flexible parsing: find two colors anywhere in the command
                color_names = [word for word in words if word in name_to_color]
                if len(color_names) < 2:
                    raise ValueError("You must specify two valid colors.")

                c1 = get_color_from_command(color_names[0])
                c2 = get_color_from_command(color_names[1])
                swap_by_color(c1, c2)

        elif "shuffle" in command:
            puzzle_grid[:] = shuffled_grid_from(goal_grid)
            selected = None
    except ValueError as e:
        last_voice_command = f"Error: {e}"  # show specific error to user
        play_sound("fail")
    except Exception as e:
        last_voice_command = "Sorry, I didn't understand."  # generic error
        print(f"[VOICE] error while handling '{command}': {e}")
    finally:
        is_processing_action = False  # always release lock


def swap_by_color(c1, c2):
    global turn_number
    pos1 = pos2 = None
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            color = puzzle_grid[r][c]
            if color == c1 and not pos1:
                pos1 = (r, c)
            elif color == c2 and not pos2:
                pos2 = (r, c)

    if not pos1 or not pos2:
        raise ValueError("One or both colors not found on the grid.")

    if are_adjacent(pos1, pos2):
        turn_number = swap_blocks(puzzle_grid, pos1, pos2, turn_number)
    else:
        raise ValueError("Tiles must be adjacent to swap.")


def swap_with_this(words, grid, hovered_cell):
    global turn_number
    if hovered_cell is None:
        raise ValueError("You must point at a tile with the mouse.")

    color_name = next(
        (w for w in words if w not in {"swap", "switch", "with", "and", "this", "that"}), None
    )
    color_rgb = get_color_from_command(color_name)
    if color_rgb is None:
        raise ValueError(f"Color '{color_name}' not recognized.")

    target = None
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if grid[r][c] == color_rgb:
                target = (r, c)
                break
        if target:
            break
    
    if not target:
        raise ValueError(f"Color '{color_name}' not found on the grid.")

    if are_adjacent(hovered_cell, target):
        turn_number = swap_blocks(grid, hovered_cell, target, turn_number)
    else:
        raise ValueError("Pointed tile and spoken color are not adjacent.")


# Spawn background thread for STT
threading.Thread(
    target=voice_listener, args=(handle_voice_command,), daemon=True
).start()


# GAME LOOP
while True:
    # MENU
    if state == GameState.MENU:
        start_btn = draw_menu()
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_btn.collidepoint(event.pos):
                    play_sound("select")
                    start_round()

    # PLAYING
    elif state == GameState.PLAYING:
        screen.fill(BACKGROUND_COLOR)

        # Draw goal grid (top)
        draw_grid(screen, goal_grid)

        # Determine hovered cell in puzzle grid
        puzzle_top = GRID_SIZE * (BLOCK_SIZE + MARGIN) + MARGIN + GAP_BETWEEN_GRIDS
        mx, my = pygame.mouse.get_pos()
        if mx >= GRID_OFFSET_X and my >= puzzle_top:
            row = (my - puzzle_top) // (BLOCK_SIZE + MARGIN)
            col = (mx - GRID_OFFSET_X) // (BLOCK_SIZE + MARGIN)
            hovered = (
                (row, col) if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE else None
            )
        else:
            hovered = None

        draw_grid(
            screen,
            puzzle_grid,
            top_offset=puzzle_top,
            highlight=selected,
            hovered=hovered,
        )

        # Win check
        if grids_match(goal_grid, puzzle_grid):
            if not won:
                stop_music()
                play_music("win_music")
                won = True
            state = GameState.GAME_OVER
            continue

        draw_game_hud()
        mute_btn_rect = draw_mute_button(screen, is_muted) # draw the mute button
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                play_sound("select")
                return_to_menu()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # new: check for mute button click first
                if mute_btn_rect.collidepoint(event.pos):
                    toggle_mute()
                elif not is_processing_action and hovered is not None:
                    if selected is None:
                        selected = hovered
                        play_sound("select")

                    elif hovered == selected:
                        selected = None # deselect

                    elif are_adjacent(selected, hovered):
                        is_processing_action = True  # lock action
                        turn_number = swap_blocks(
                            puzzle_grid, selected, hovered, turn_number
                        )
                        selected = None
                        is_processing_action = False  # release lock
                    else:
                        play_sound("fail") # feedback for non-adjacent click
                        selected = hovered


    # GAME OVER
    elif state == GameState.GAME_OVER:
        back_btn = draw_game_over()
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                play_sound("select")
                return_to_menu()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_btn.collidepoint(event.pos):
                    play_sound("select")
                    return_to_menu()

    clock.tick(60)