"""
GAME:BitHigh
MEMBERS:
  -Bocalan, Rachel
  -Carpizo, Eunice
  -Tudayan, Matt Jhardy
"""

# ==============================================================================
# IMPORTS
# ==============================================================================
import pygame, os, sys, json, random
from ffpyplayer.player import MediaPlayer

# ==============================================================================
# INITIALIZATION
# ==============================================================================
pygame.init()
pygame.display.set_caption("BitHigh")
pygame.display.set_icon(pygame.image.load("BitHighIcon.png"))

SCREEN_WIDTH  = 686
SCREEN_HEIGHT = 768
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock  = pygame.time.Clock()


RED, GREEN, YELLOW = "\033[31m", "\033[32m", "\033[33m"
BLUE, MAGENTA, CYAN = "\033[34m", "\033[35m", "\033[36m"

# ==============================================================================
# UTILITIES
# ==============================================================================
def resource_path(relative):
    """Locate bundled resources correctly whether running from source or .exe."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
    return os.path.join(base, relative)

def load_scaled_image(path, size):
    return pygame.transform.scale(pygame.image.load(resource_path(path)), size)

# ==============================================================================
# POPUP
# ==============================================================================
class Popup:
    OFFSCREEN_Y  = -400
    SLIDE_SPEED  = 35
    BOB_STRENGTH = -8
    GRAVITY      = 1.2
    BOB_DAMPEN   = 0.55
    BOB_STOP     = 1.5
    SLIDE_OUT_SPD = 22

    def __init__(self, image_path, size, target_y, unclickable=True):
        self.image      = load_scaled_image(image_path, size)
        self.rect       = self.image.get_rect(centerx=SCREEN_WIDTH // 2, top=self.OFFSCREEN_Y)
        self.target_y   = target_y
        self.unclickable = unclickable
        self.state      = None
        self.vel        = 0.0
        self.active     = False

    def open(self, sound=None):
        self.rect.top = self.OFFSCREEN_Y
        self.vel = self.SLIDE_SPEED
        self.state = 'slide_in'
        self.active = True
        if sound:
            sound.play()

    def close(self):
        if self.active and self.state != 'slide_out':
            self.vel   = self.SLIDE_OUT_SPD
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
            if self.rect.top >= self.target_y:
                self.rect.top = self.target_y
                self.vel      = self.BOB_STRENGTH
                self.state    = 'bob'

        elif self.state == 'bob':
            self.vel      += self.GRAVITY
            self.rect.top += int(self.vel)
            if self.rect.top >= self.target_y and self.vel > 0:
                self.rect.top = self.target_y
                self.vel      = self.vel * -self.BOB_DAMPEN
                if abs(self.vel) < self.BOB_STOP:
                    self.vel   = 0
                    self.state = None

        elif self.state == 'slide_out':
            self.rect.top += self.vel
            if self.rect.top > SCREEN_HEIGHT:
                self.active = False
                self.state  = None

    def draw(self, surface):
        if not self.active:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        surface.blit(self.image, self.rect)

# ==============================================================================
# BUTTON
# ==============================================================================
class Button:
    def __init__(self, image1_path, image2_path, position, size):
        self.image_normal  = load_scaled_image(image1_path, size)
        self.image_pressed = load_scaled_image(image2_path, size)
        self.current_image = self.image_normal
        self.rect          = self.current_image.get_rect(center=position)
        self.is_holding    = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.is_holding    = True
                self.current_image = self.image_pressed
                return False

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_holding    = self.is_holding
            self.is_holding    = False
            self.current_image = self.image_normal
            if was_holding and self.rect.collidepoint(event.pos):
                return True

        return False

    def draw(self, surface):
        surface.blit(self.current_image, self.rect)

# ==============================================================================
# FADE TRANSITION
# ==============================================================================
class Fade:
    FADE_IN_SPEED  = 5
    FADE_OUT_SPEED = 5

    def __init__(self):
        self.overlay    = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.overlay.fill((15, 58, 78))
        self.alpha      = 0
        self.state      = None
        self.on_complete = None

    @property
    def active(self):
        return self.state is not None

    def start(self, on_peak_callback=None):
        self.alpha       = 0
        self.state       = 'fade_in'
        self.on_complete = on_peak_callback

    def update(self):
        if self.state == 'fade_in':
            self.alpha = min(255, self.alpha + self.FADE_IN_SPEED)
            if self.alpha >= 255:
                if self.on_complete:
                    self.on_complete()
                    self.on_complete = None
                self.state = 'fade_out'

        elif self.state == 'fade_out':
            self.alpha = max(0, self.alpha - self.FADE_OUT_SPEED)
            if self.alpha <= 0:
                self.state = None

    def draw(self, surface):
        if self.state is None:
            return
        self.overlay.set_alpha(self.alpha)
        surface.blit(self.overlay, (0, 0))

# ==============================================================================
# GAME STATE
# ==============================================================================
class GameState:
    def __init__(self):
        self.running       = True
        self.playing_video = True
        self.week          = 0
        self.scene         = "menu"
        self.gender        = None
        self.selected_char = None

# ==============================================================================
# ASSET LOADING
# ==============================================================================
CHAR_IMG_SIZE = (217, 193)

def load_chars_from_json(json_file, char_images):
    # Load a character JSON and preload all appearance images into char_images.
    with open(resource_path(json_file), "r") as f:
        chars = json.load(f)
    for char in chars:
        key = char['Appearance']
        if key not in char_images:
            char_images[key] = load_scaled_image(key, CHAR_IMG_SIZE)
    return chars

def load_assets():
    assets = {}

    assets['intro_video']      = MediaPlayer(resource_path("GameIntro.mov"))
    assets['button_click']     = pygame.mixer.Sound(resource_path("ButtonClicked.mp3"))
    assets['slide_in']         = pygame.mixer.Sound(resource_path("slide_in.mp3"))
    assets['skip_clicked']     = pygame.mixer.Sound(resource_path("skip_clicked.mp3"))
    assets['main_game_image']  = load_scaled_image("MainGame.png",  (SCREEN_WIDTH, SCREEN_HEIGHT))
    assets['main_menu_image']  = load_scaled_image("Menu.png",      (SCREEN_WIDTH, SCREEN_HEIGHT))

    assets['char_images'] = {}
    assets['boys_chars']  = load_chars_from_json("BoysChar.json",  assets['char_images'])
    assets['girls_chars'] = load_chars_from_json("GirlsChar.json", assets['char_images'])

    return assets

# ==============================================================================
# BUTTON / POPUP CREATION
# ==============================================================================
def create_buttons():
    return {
        # Main menu
        'start_game': Button("StartGameButton.png", "StartGameAnimation.png", (338, 385), (474, 109)),
        'details':    Button("DetailsButton.png",   "DetailsAnimation.png",   (338, 565), (474, 109)),
        # Gender popup
        'girl': Button("FemaleButton.png", "FemaleButtonAnimation.png", (0, 0), (406, 89)),
        'boy':  Button("MaleButton.png",   "MaleButtonAnimation.png",   (0, 0), (406, 89)),
        # Game scene
        'skip': Button("Skip.png", "SkipAnimation.png", (120, 655), (128, 130)),
        # NCE popup buttons
        'nce_btn1':    Button("NCE_button1.png",    "NCE_button1_anim.png",    (0, 0), (500, 76)),
        'nce_btn2':    Button("NCE_button2.png",    "NCE_button2_anim.png",    (0, 0), (500, 76)),
        'nce_btn3':    Button("NCE_button3.png",    "NCE_button3_anim.png",    (0, 0), (500, 76)),
        'nce_surprise':Button("Surprise_me.png",    "Surprise_me_anim.png",    (0, 0), (284, 44)),
    }

def create_popups():
    return {
        'details': Popup("DetailsPopup.png", (613, 727), target_y=15),
        'gender':  Popup("GenderPopup.png",  (517, 615), target_y=80, unclickable=False),
        'nce':     Popup("NCE_popup.png",    (583, 695), target_y=40, unclickable=False),  # adjust size/target_y to fit your image
    }

# ==============================================================================
# VIDEO PLAYBACK
# ==============================================================================
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
        img, _ = frame
        surface = pygame.transform.scale(
            pygame.image.frombuffer(img.to_bytearray()[0], img.get_size(), 'RGB'),
            (SCREEN_WIDTH, SCREEN_HEIGHT))
        screen.blit(surface, (0, 0))

# ==============================================================================
# MENU SCENE — EVENT HANDLING
# ==============================================================================
def handle_menu_events(buttons, popups, game_state, event, blue_fade, assets):
    if blue_fade.active:
        return  # Block input during transition

    gender_popup  = popups['gender']
    details_popup = popups['details']

    if gender_popup.active:
        gender_popup.handle_event(event)

        if buttons['girl'].handle_event(event):
            assets['button_click'].play()
            game_state.gender        = "girl"
            game_state.selected_char = random.choice(assets['girls_chars'])
            gender_popup.close()
            blue_fade.start(on_peak_callback=lambda: setattr(game_state, 'scene', 'game'))

        if buttons['boy'].handle_event(event):
            assets['button_click'].play()
            game_state.gender        = "boy"
            game_state.selected_char = random.choice(assets['boys_chars'])
            gender_popup.close()
            blue_fade.start(on_peak_callback=lambda: setattr(game_state, 'scene', 'game'))

    elif details_popup.active:
        details_popup.handle_event(event)

    else:
        if buttons['details'].handle_event(event):
            assets['button_click'].play()
            details_popup.open(sound=assets['slide_in'])

        if buttons['start_game'].handle_event(event):
            assets['button_click'].play()
            gender_popup.open(sound=assets['slide_in'])

def handle_game_events(buttons, popups, game_state, event, blue_fade, assets):
    if blue_fade.active:
        return

    if buttons['skip'].handle_event(event):
        assets['skip_clicked'].play()
        popups['nce'].open(sound=assets['slide_in'])

    # NCE popup button handling
    if popups['nce'].active:
        popups['nce'].handle_event(event)

        if buttons['nce_btn1'].handle_event(event):
            assets['button_click'].play()
            popups['nce'].close()

        if buttons['nce_btn2'].handle_event(event):
            assets['button_click'].play()
            popups['nce'].close()

        if buttons['nce_btn3'].handle_event(event):
            assets['button_click'].play()
            popups['nce'].close()

        if buttons['nce_surprise'].handle_event(event):
            assets['button_click'].play()
            popups['nce'].close()

# ==============================================================================
# MENU SCENE — DRAWING
# ==============================================================================
def draw_menu(screen, buttons, popups):
    for name, button in buttons.items():
        if name not in ('girl', 'boy', 'skip'):
            button.draw(screen)

    for popup in popups.values():
        popup.update()
        popup.draw(screen)

    # Pin gender buttons to the popup's current position
    if popups['gender'].active:
        popup_top = popups['gender'].rect.top
        buttons['boy'].rect.center  = (337, popup_top + 293)
        buttons['girl'].rect.center = (337, popup_top + 443)
        buttons['boy'].draw(screen)
        buttons['girl'].draw(screen)

# ==============================================================================
# GAME SCENE — DRAWING
# ==============================================================================
def draw_game(screen, assets, game_state, buttons, popups):
    screen.blit(assets['main_game_image'], (0, 0))

    if game_state.selected_char:
        face_img = assets['char_images'][game_state.selected_char['Appearance']]
        screen.blit(face_img, (116, 105))

    buttons['skip'].draw(screen)

    # NCE popup
    popups['nce'].update()
    popups['nce'].draw(screen)

    if popups['nce'].active:
        popup_top = popups['nce'].rect.top
        # Adjust Y offsets below to match your NCE_popup.png button positions
        buttons['nce_btn1'].rect.center    = (349, popup_top + 335)
        buttons['nce_btn2'].rect.center    = (349, popup_top + 430)
        buttons['nce_btn3'].rect.center    = (349, popup_top + 520)
        buttons['nce_surprise'].rect.center = (355, popup_top + 601)
        buttons['nce_btn1'].draw(screen)
        buttons['nce_btn2'].draw(screen)
        buttons['nce_btn3'].draw(screen)
        buttons['nce_surprise'].draw(screen)

# ==============================================================================
# MAIN LOOP
# ==============================================================================
def main():
    assets     = load_assets()
    buttons    = create_buttons()
    popups     = create_popups()
    game_state = GameState()
    blue_fade  = Fade()

    while game_state.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_state.running = False

            if not game_state.playing_video and game_state.scene == "menu":
                handle_menu_events(buttons, popups, game_state, event, blue_fade, assets)

            elif not game_state.playing_video and game_state.scene == "game":
                handle_game_events(buttons, popups, game_state, event, blue_fade, assets)

        # --- Draw ---
        if game_state.playing_video:
            handle_video(assets, game_state)

        elif game_state.scene == "menu":
            screen.blit(assets['main_menu_image'], (0, 0))
            draw_menu(screen, buttons, popups)
            blue_fade.update()
            blue_fade.draw(screen)

        elif game_state.scene == "game":
            draw_game(screen, assets, game_state, buttons, popups)
            blue_fade.update()
            blue_fade.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

# ==============================================================================
# ENTRY POINT
# ==============================================================================
if __name__ == "__main__":
    main()
