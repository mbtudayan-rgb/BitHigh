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
pygame.display.set_caption("BitHigh") #Displays Caption of the Game
pygame.display.set_icon(pygame.image.load("BitHighIcon.png")) #Displays the Icon of the game


# Screen setup
SCREEN_WIDTH = 686 #Width of the screen
SCREEN_HEIGHT = 768 #Height of the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)) #Sets the size of the screen
clock = pygame.time.Clock() #Controls the game's frame rate
RED     = "\033[31m" #Color's the word's Red
GREEN   = "\033[32m" #Color's the word's Green
YELLOW  = "\033[33m" #Color's the word's Yellow
BLUE    = "\033[34m" #Color's the word's Blue
MAGENTA = "\033[35m" #Color's the word's Magenta
CYAN    = "\033[36m" #Color's the word's Cyan

# ------------------------------------------------------------------------------
# UTILITY FUNCTIONS
# ------------------------------------------------------------------------------
#Para lang sa video, it won't work without this, IDK what it does but its important said by the video
def resource_path(relative):
   base = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
   return os.path.join(base, relative)


# ------------------------------------------------------------------------------
# POPUP CLASS
# ------------------------------------------------------------------------------
class Popup:
    TARGET_Y      = 15           # final resting Y position
    OFFSCREEN_Y   = -400         # starting / exit Y position
    SLIDE_SPEED   = 18           # pixels per frame falling down
    BOB_STRENGTH  = -8           # upward bounce velocity
    GRAVITY       = 1.2          # pulls popup back down during bob
    BOB_DAMPEN    = 0.55         # how much bounce energy is kept
    BOB_STOP      = 1.5          # velocity threshold to stop bobbing
    SLIDE_OUT_SPD = 22           # pixels per frame sliding out

    def __init__(self, image_path, size):
        self.image = pygame.transform.scale(
            pygame.image.load(resource_path(image_path)), size)
        self.size = size
        self.rect = self.image.get_rect(
            centerx = SCREEN_WIDTH // 2, top=self.OFFSCREEN_Y)
        self.state = None
        self.vel = 0.0
        self.active = False

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
            if self.rect.collidepoint(event.pos):
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
                self.vel = self.BOB_STRENGTH   # first upward bounce
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
                self.state  = None

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
        self.show_details_popup = False
        self.popup_anim_state = None
        self.popup_y = -400
        self.popup_vel = 0

# ------------------------------------------------------------------------------
# LOAD ASSETS
# ------------------------------------------------------------------------------
def load_assets():
   assets = {}


   # Video
   assets['intro_video'] = MediaPlayer(resource_path("GameIntro.mp4"))


   # Main Game Background
   assets['main_game_image'] = pygame.transform.scale(
       pygame.image.load(resource_path("MainGame.png")),
       (SCREEN_WIDTH, SCREEN_HEIGHT))


   assets['main_menu_image'] = pygame.transform.scale(
       pygame.image.load(resource_path("Menu.png")),
       (SCREEN_WIDTH, SCREEN_HEIGHT))


   return assets

# ------------------------------------------------------------------------------
# CREATIONS OF ANYTHING NALANG
# ------------------------------------------------------------------------------
def create_buttons():
    buttons = {}

    buttons['start_game'] = Button(
        "StartGameButton.png", "StartGameAnimation.png",
        (338, 385), (474, 109))

    buttons['details'] = Button(
        "DetailsButton.png", "DetailsAnimation.png",
        (338, 565), (474, 109))

    return buttons


def create_popups():
    popups = {}

    popups['details'] = Popup("DetailsPopup.png", (613, 727))

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
def handle_main_game(buttons, popups, game_state, event):
    screen.blit(assets['main_menu_image'], (0, 0))

    details_popup = popups['details']

    if not details_popup.active:
        if buttons['details'].handle_event(event):
            details_popup.open()
        buttons['start_game'].handle_event(event)
    else:
        details_popup.handle_event(event)

    for button in buttons.values():
        button.draw(screen)

    details_popup.update()
    details_popup.draw(screen)

# ------------------------------------------------------------------------------
# MAIN PROGRAM
# ------------------------------------------------------------------------------
def main():
    global assets
    assets  = load_assets()
    buttons = create_buttons()
    popups  = create_popups()
    game_state = GameState()

    while game_state.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_state.running = False

            if not game_state.playing_video:
                handle_main_game(buttons, popups, game_state, event)

        if game_state.playing_video:
            handle_video(assets, game_state)
        else:
            if not pygame.event.peek():
                screen.blit(assets['main_menu_image'], (0, 0))
                for button in buttons.values():
                    button.draw(screen)
                for popup in popups.values():
                    popup.update()
                    popup.draw(screen)

        pygame.display.flip()
        clock.tick(120)

    pygame.quit()

# ------------------------------------------------------------------------------
# RUN GAME
# ------------------------------------------------------------------------------
if __name__ == "__main__":
   main()