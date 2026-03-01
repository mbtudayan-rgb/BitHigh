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

# ------------------------------------------------------------------------------
# INITIALIZATION
# ------------------------------------------------------------------------------
pygame.init()
pygame.display.set_caption("BitHigh")
pygame.display.set_icon(pygame.image.load("BitHighIcon.png"))

# Screen setup
SCREEN_WIDTH = 1366
SCREEN_HEIGHT = 768
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 20)


# ------------------------------------------------------------------------------
# UTILITY FUNCTIONS
# ------------------------------------------------------------------------------
def resource_path(relative):
    base = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
    return os.path.join(base, relative)


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
            if event.button == 1:
                was_holding = self.is_holding
                self.is_holding = False
                self.current_image = self.image_normal
                if was_holding and self.rect.collidepoint(event.pos):
                    return True

        return False

    def draw(self, surface):
        surface.blit(self.current_image, self.rect)


# ------------------------------------------------------------------------------
# GAME STATE
# ------------------------------------------------------------------------------
class GameState:
    def __init__(self):
        self.running = True
        self.playing_video = True
        self.week = 0
        self.show_text = False


# ------------------------------------------------------------------------------
# LOAD ASSETS
# ------------------------------------------------------------------------------
def load_assets():
    assets = {}

    # Video
    assets['intro_video'] = MediaPlayer(resource_path("GameIntro.mp4"))

    # Background
    assets['main_game_image'] = pygame.transform.scale(
        pygame.image.load(resource_path("MainGame.jpg")),
        (SCREEN_WIDTH, SCREEN_HEIGHT)
    )
    return assets


# ------------------------------------------------------------------------------
# CREATE BUTTONS
# ------------------------------------------------------------------------------
def create_buttons():
    buttons = {}


    buttons['skip'] = Button(
        "SkipButton1.png",
        "SkipButton2.png",
        (1013, 610),
        (215, 215)
    )

    buttons['involvements'] = Button(
        "InvolvementsButton1.png",
        "InvolvementsButton2.png",
        (743, 649),
        (70, 70)
    )

    buttons['activities'] = Button(
        "ActivitiesButton1.png",
        "ActivitiesButton2.png",
        (843.5, 649),
        (70, 70)
    )

    buttons['relationships'] = Button(
        "RelationshipButton1.png",
        "RelationshipsButton2.png",
        (1181.5, 649),
        (70, 70)
    )

    buttons['menu'] = Button(
        "MenuButton1.png",
        "MenuButton2.png",
        (1281.5, 649),
        (70, 70)
    )

    return buttons


# ------------------------------------------------------------------------------
# VIDEO PLAYBACK
# ------------------------------------------------------------------------------
def handle_video(assets, game_state):
    frame, val = assets['intro_video'].get_frame()

    if val == 'eof':
        game_state.playing_video = False
        screen.blit(assets['main_game_image'], (0, 0))
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
def handle_main_game(buttons, game_state, event):
    # Draw background
    screen.blit(assets['main_game_image'], (0, 0))

    # Handle button events
    if (buttons['skip'].handle_event(event) or
            buttons['involvements'].handle_event(event) or
            buttons['activities'].handle_event(event) or
            buttons['relationships'].handle_event(event) or
            buttons['menu'].handle_event(event)):
        pass

    # Draw all buttons
    for button in buttons.values():
        button.draw(screen)

    # Show text if week has advanced
    if game_state.show_text:
        text_surface = font.render("hi", True, (1, 47, 71))
        screen.blit(text_surface, (300, 300))

    if game_state.week == 1:
        game_state.show_text = True


# ------------------------------------------------------------------------------
# MAIN PROGRAM
# ------------------------------------------------------------------------------
def main():
    global assets
    assets = load_assets()
    buttons = create_buttons()
    game_state = GameState()

    # Main game loop
    while game_state.running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_state.running = False

            # Only handle game events if not playing video
            if not game_state.playing_video:
                handle_main_game(buttons, game_state, event)

        # Handle video playback
        if game_state.playing_video:
            handle_video(assets, game_state)
        else:
            # Redraw main game if no events (prevents flickering)
            if not pygame.event.peek():
                screen.blit(assets['main_game_image'], (0, 0))
                for button in buttons.values():
                    button.draw(screen)
                if game_state.show_text:
                    text_surface = font.render("hi", True, (1, 47, 71))
                    screen.blit(text_surface, (300, 300))

        # Update display
        pygame.display.flip()
        clock.tick(60)

    # Cleanup
    pygame.quit()


# ------------------------------------------------------------------------------
# RUN GAME
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    main()