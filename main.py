"""
GAME:BitHigh
MEMBERS:
  -Bocalan, Rachel
  -Carpizo, Eunice
  -Tudayan, Matt Jhardy
"""

# ------------------------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------------------------
import pygame
import os
import sys
from ffpyplayer.player import MediaPlayer
import json
import random

# ------------------------------------------------------------------------------
# INITIALIZATION
# ------------------------------------------------------------------------------
pygame.init()
pygame.display.set_caption("BitHigh")  # Displays Caption of the Game
pygame.display.set_icon(pygame.image.load("BitHighIcon.png"))  # Displays the Icon of the game

# Screen setup
SCREEN_WIDTH = 686  # Width of the screen
SCREEN_HEIGHT = 768  # Height of the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))  # Sets the size of the screen
clock = pygame.time.Clock()  # Controls the game's frame rate
RED = "\033[31m"  # Color's the word's Red
GREEN = "\033[32m"  # Color's the word's Green
YELLOW = "\033[33m"  # Color's the word's Yellow
BLUE = "\033[34m"  # Color's the word's Blue
MAGENTA = "\033[35m"  # Color's the word's Magenta
CYAN = "\033[36m"  # Color's the word's Cyan


# ------------------------------------------------------------------------------
# UTILITY FUNCTIONS
# ------------------------------------------------------------------------------
# Helps to locate the resources correctly
def resource_path(relative):
    base = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
    return os.path.join(base, relative)


# ------------------------------------------------------------------------------
# POPUP CLASS
# ------------------------------------------------------------------------------
class Popup:
    TARGET_Y = 15  # final resting Y position
    OFFSCREEN_Y = -400  # starting / exit Y position
    SLIDE_SPEED = 18  # pixels per frame falling down
    BOB_STRENGTH = -8  # upward bounce velocity
    GRAVITY = 1.2  # pulls popup back down during bob
    BOB_DAMPEN = 0.55  # how much bounce energy is kept
    BOB_STOP = 1.5  # velocity threshold to stop bobbing
    SLIDE_OUT_SPD = 22  # pixels per frame sliding out

    def __init__(self, image_path, size, target_y, unclickable=True):
        self.image = pygame.transform.scale(
            pygame.image.load(resource_path(image_path)), size)
        self.size = size
        self.rect = self.image.get_rect(
            centerx=SCREEN_WIDTH // 2, top=self.OFFSCREEN_Y)
        self.state = None
        self.vel = 0.0
        self.active = False
        self.TARGET_Y = target_y
        self.unclickable = unclickable

    def open(self):
        self.rect.top = self.OFFSCREEN_Y
        self.vel = self.SLIDE_SPEED
        self.state = 'slide_in'
        self.active = True

    def close(self):
        if self.active and self.state != 'slide_out':
            self.vel = self.SLIDE_OUT_SPD
            self.state = 'slide_out'

    def handle_event(self, event):
        if not self.active:
            return False
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.rect.collidepoint(event.pos) and self.unclickable:
                self.close()
                return True
        return False

    def update(self):
        if not self.active:
            return

        if self.state == 'slide_in':
            self.rect.top += self.vel
            if self.rect.top >= self.TARGET_Y:
                self.rect.top = self.TARGET_Y
                self.vel = self.BOB_STRENGTH  # first upward bounce
                self.state = 'bob'

        elif self.state == 'bob':
            self.vel += self.GRAVITY
            self.rect.top += int(self.vel)
            if self.rect.top >= self.TARGET_Y and self.vel > 0:
                self.rect.top = self.TARGET_Y
                self.vel = self.vel * -self.BOB_DAMPEN  # reverse & dampen
                if abs(self.vel) < self.BOB_STOP:
                    self.vel = 0
                    self.state = None

        elif self.state == 'slide_out':
            self.rect.top += self.vel
            if self.rect.top > SCREEN_HEIGHT:
                self.active = False
                self.state = None

    def draw(self, surface):
        if not self.active:
            return

        # Semi-transparent black overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        # Popup image
        surface.blit(self.image, self.rect)


# ------------------------------------------------------------------------------
# BUTTON CLASS
# ------------------------------------------------------------------------------
class Button:
    def __init__(self, image1_path, image2_path, position, size):
        self.image_normal = pygame.transform.scale(pygame.image.load(
            resource_path(image1_path)), size)
        self.image_pressed = pygame.transform.scale(pygame.image.load(
            resource_path(image2_path)), size)
        self.current_image = self.image_normal
        self.rect = self.current_image.get_rect(center=position)
        self.is_holding = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.is_holding = True
                self.current_image = self.image_pressed
                return False

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.is_holding:
                was_holding = self.is_holding
                self.is_holding = False
                self.current_image = self.image_normal
                if was_holding and self.rect.collidepoint(event.pos):
                    return True

        return False

    def draw(self, surface):
        surface.blit(self.current_image, self.rect)


# ------------------------------------------------------------------------------
# BLUE FADE TRANSITION
# ------------------------------------------------------------------------------
class Fade:
    FADE_IN_SPEED = 10  # alpha added per frame (fade to blue)
    FADE_OUT_SPEED = 10  # alpha removed per frame (fade to game)

    def __init__(self):
        self.overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.overlay.fill((15, 58, 78))  # Cyan color
        self.alpha = 0
        self.state = None
        self.on_complete = None

    def start(self, on_peak_callback=None):
        self.alpha = 0
        self.state = 'fade_in'
        self.on_complete = on_peak_callback

    @property
    def active(self):
        return self.state is not None

    def update(self):
        if self.state == 'fade_in':
            self.alpha = min(255, self.alpha + self.FADE_IN_SPEED)
            if self.alpha >= 255:
                self.alpha = 255
                if self.on_complete:
                    self.on_complete()
                    self.on_complete = None
                self.state = 'fade_out'

        elif self.state == 'fade_out':
            self.alpha = max(0, self.alpha - self.FADE_OUT_SPEED)
            if self.alpha <= 0:
                self.alpha = 0
                self.state = None

    def draw(self, surface):
        if self.state is None:
            return
        self.overlay.set_alpha(self.alpha)
        surface.blit(self.overlay, (0, 0))


# ------------------------------------------------------------------------------
# GAME STATE
# ------------------------------------------------------------------------------
class GameState:
    def __init__(self):
        self.running = True
        self.playing_video = True
        self.week = 0
        self.scene = "menu"
        self.show_details_popup = False
        self.popup_anim_state = None
        self.popup_y = -400
        self.popup_vel = 0
        self.gender = None
        self.selected_char = None


# ------------------------------------------------------------------------------
# LOAD ASSETS
# ------------------------------------------------------------------------------
def load_assets():
    assets = {}

    assets['intro_video'] = MediaPlayer(resource_path("GameIntro.mp4"))
    assets['button_click'] = pygame.mixer.Sound(resource_path("ButtonClicked.mp3"))

    assets['main_game_image'] = pygame.transform.scale(
        pygame.image.load(resource_path("MainGame.png")), (SCREEN_WIDTH, SCREEN_HEIGHT))

    assets['main_menu_image'] = pygame.transform.scale(
        pygame.image.load(resource_path("Menu.png")), (SCREEN_WIDTH, SCREEN_HEIGHT))

    # Load JSON + preload character images
    assets['char_images'] = {}
    with open(resource_path("BoysChar.json"), "r") as f:
        assets['boys_chars'] = json.load(f)
    for char in assets['boys_chars']:
        img = pygame.transform.scale(
            pygame.image.load(resource_path(char['Appearance'])),
            (193, 171))
        assets['char_images'][char['Appearance']] = img

    return assets


# ------------------------------------------------------------------------------
# CREATIONS
# ------------------------------------------------------------------------------
def create_buttons():
    buttons = {}
    # ---MAIN MENU---
    buttons['start_game'] = Button(
        "StartGameButton.png", "StartGameAnimation.png",
        (338, 385), (474, 109))

    buttons['details'] = Button(
        "DetailsButton.png", "DetailsAnimation.png",
        (338, 565), (474, 109))

    # ---GENDER POPUP---
    buttons['girl'] = Button(
        "FemaleButton.png", "FemaleButtonAnimation.png",
        (0, 0), (406, 89))

    buttons['boy'] = Button(
        "MaleButton.png", "MaleButtonAnimation.png",
        (0, 0), (406, 89))

    # ---NCE POPUP---
    return buttons


def create_popups():
    popups = {}

    popups['details'] = Popup("DetailsPopup.png", (613, 727), target_y=15)
    popups['gender'] = Popup("GenderPopup.png", (517, 615), target_y=80, unclickable=False)

    return popups


# ------------------------------------------------------------------------------
# VIDEO PLAYBACK
# ------------------------------------------------------------------------------
def handle_video(assets, game_state):
    frame, val = assets['intro_video'].get_frame()

    if val == 'eof':
        print(fr"""{CYAN}
_     _  _______  ___      _______  _______  __   __  _______
| | _ | ||       ||   |    |       ||       ||  |_|  ||       |
| || || ||    ___||   |    |       ||   _   ||       ||    ___|
|       ||   |___ |   |    |       ||  | |  ||       ||   |___
|       ||    ___||   |___ |      _||  |_|  ||       ||    ___|
|   _   ||   |___ |       ||     |_ |       || ||_|| ||   |___
|__| |__||_______||_______||_______||_______||_|   |_||_______|""")
        print(f"{BLUE}Start a Scholar's Academic Life!")
        game_state.playing_video = False
        screen.blit(assets['main_menu_image'], (0, 0))
        pygame.display.update()
        assets['intro_video'].close_player()
        return

    if frame is not None:
        img, t = frame
        surface = pygame.image.frombuffer(
            img.to_bytearray()[0],
            img.get_size(),
            'RGB'
        )
        surface = pygame.transform.scale(surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(surface, (0, 0))


# ------------------------------------------------------------------------------
# MAIN GAME LOOP
# ------------------------------------------------------------------------------
def handle_main_game(buttons, popups, game_state, event, blue_fade, assets):
    details_popup = popups['details']
    gender_popup = popups['gender']

    # Block all input while the cyan fade is playing
    if blue_fade.active:
        return

    if gender_popup.active:
        gender_popup.handle_event(event)

        if buttons['girl'].handle_event(event):
            print("Girl :P")
            assets['button_click'].play()
            game_state.gender = "girl"
            gender_popup.close()
            blue_fade.start(on_peak_callback=lambda: setattr(game_state, 'scene', 'game'))

        if buttons['boy'].handle_event(event):
            assets['button_click'].play()
            game_state.gender = "boy"
            game_state.selected_char = random.choice(assets['boys_chars'])
            gender_popup.close()
            blue_fade.start(on_peak_callback=lambda: setattr(game_state, 'scene', 'game'))

    elif details_popup.active:
        details_popup.handle_event(event)
    else:
        if buttons['details'].handle_event(event):
            assets['button_click'].play()
            details_popup.open()
        if buttons['start_game'].handle_event(event):
            assets['button_click'].play()
            gender_popup.open()


def handle_game_scene(assets, game_state):
    screen.blit(assets['main_game_image'], (0, 0))

    if game_state.selected_char:
        face_key = game_state.selected_char['Appearance']
        face_img = assets['char_images'][face_key]
        screen.blit(face_img, (140, 100))


# ------------------------------------------------------------------------------
# MAIN PROGRAM
# ------------------------------------------------------------------------------
def main():
    global assets
    assets = load_assets()
    buttons = create_buttons()
    popups = create_popups()
    game_state = GameState()
    blue_fade = Fade()

    while game_state.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_state.running = False

            if not game_state.playing_video:
                if game_state.scene == "menu":
                    handle_main_game(buttons, popups, game_state, event, blue_fade, assets)

        if game_state.playing_video:
            handle_video(assets, game_state)

        elif game_state.scene == "menu":
            screen.blit(assets['main_menu_image'], (0, 0))

            for name, button in buttons.items():
                if name not in ('girl', 'boy'):
                    button.draw(screen)

            for popup in popups.values():
                popup.update()
                popup.draw(screen)

            if popups['gender'].active:
                popup_top = popups['gender'].rect.top
                buttons['girl'].rect.center = (337, popup_top + 443)
                buttons['boy'].rect.center = (337, popup_top + 293)
                buttons['girl'].draw(screen)
                buttons['boy'].draw(screen)

            blue_fade.update()
            blue_fade.draw(screen)


        elif game_state.scene == "game":
            handle_game_scene(assets, game_state)

            blue_fade.update()
            blue_fade.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


# ------------------------------------------------------------------------------
# RUN GAME
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
