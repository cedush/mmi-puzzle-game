# sound_manager.py
import pygame

pygame.mixer.init()

# Load sounds
sounds = {
    "select": pygame.mixer.Sound("sounds/select.mp3"),
    "swap": pygame.mixer.Sound("sounds/swap11labs.mp3"),
    "fail": pygame.mixer.Sound("sounds/fail11labs.mp3"),
    "win_music": "sounds/won.mp3",
    "bg_music": "sounds/background.mp3"
}

def play_sound(name):
    if name in sounds and isinstance(sounds[name], pygame.mixer.Sound):
        pygame.mixer.Sound.play(sounds[name])

def play_music(name, loops=1):
    pygame.mixer.music.stop()
    pygame.mixer.music.unload()
    pygame.mixer.music.load(sounds[name])
    pygame.mixer.music.play(loops=loops)

def stop_music():
    pygame.mixer.music.stop()
    pygame.mixer.music.unload()
