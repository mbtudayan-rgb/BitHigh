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
pygame.display.set_icon(pygame.image.load("Assets/BitHighIcon.png"))

SCREEN_WIDTH  = 686
SCREEN_HEIGHT = 768
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock  = pygame.time.Clock()


RED, GREEN, YELLOW = "\033[31m", "\033[32m", "\033[33m"
BLUE, MAGENTA, CYAN = "\033[34m", "\033[35m", "\033[36m"
RESET = "\033[0m"
BOLD  = "\033[1m"

# ==============================================================================
# UTILITIES
# ==============================================================================
def resource_path(relative):
    base = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
    return os.path.join(base, relative)

def load_scaled_image(path, size):
    return pygame.transform.scale(pygame.image.load(resource_path(path)), size)

# ==============================================================================
# QUIZ
# ==============================================================================
def run_nce_quiz(json_file="JSON/NCE.json"):

    with open(resource_path(json_file), "r") as f:
        all_questions = json.load(f)

    # Group questions by subject
    subjects = {}
    for q in all_questions:
        subj = q["Subject"]
        if subj not in subjects:
            subjects[subj] = []
        subjects[subj].append(q)

    # Shuffle subject order AND questions within each subject
    subject_order = list(subjects.keys())
    random.shuffle(subject_order)
    for subj in subject_order:
        random.shuffle(subjects[subj])

    score = 0
    total = sum(len(subjects[s]) for s in subject_order)  # 12 total
    question_num = 1

    for subj in subject_order:
        # Subject header
        print(f"\n{CYAN}{BOLD}{'='*55}")
        print(f"  {subj}!!!")
        print(f"{'='*55}{RESET}")

        for q in subjects[subj]:
            print(f"\n{BOLD}Question {question_num} of {total}:{RESET}")
            print(f"{MAGENTA}{q['Question']}{RESET}")
            print(f"  {q['A']}")
            print(f"  {q['B']}")
            print(f"  {q['C']}")

            while True:
                raw = input(f"\n{YELLOW}Your answer (A/B/C): {RESET}").strip().upper()
                if raw in ("A", "B", "C"):
                    break
                print(f"{RED}  Please type A, B, or C only!{RESET}")

            correct_letter = q["Answer"].split(".")[0].strip().upper()
            if raw == correct_letter:
                print(f"{GREEN}  ✓ Correct!{RESET}")
                score += 1
            else:
                print(f"{RED}  ✗ Wrong! The answer was: {q['Answer']}{RESET}")
            question_num += 1

    # Final results
    print(f"\n{BOLD}NCE Complete!  Score: {score}/{total}")
    if score >= 8:
        print(f"Nice work! Keep it up! 🌟📚✨")
    else:
        print(f"Yikes... better hit the books! 😬📖💀")
        print(f"You got {7 - score + 1} more wrong than passing... 😅{RESET}\n")
    return score

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
        self.pending_quiz  = False
        self.hp         = [0, 0, 0, 0, 0]
        self.hp_display = [0.0, 0.0, 0.0, 0.0, 0.0]

    def apply_char_stats(self, char):
        self.hp = [
            char.get("starting_stress",        20),
            char.get("starting_happiness",     40),
            char.get("starting_grades",        30),
            char.get("starting_intelligence",   0),
        ]
        self.hp_display = [float(v) for v in self.hp]

# ==============================================================================
# ASSET LOADING
# ==============================================================================
CHAR_IMG_SIZE = (700, 382)

def load_chars_from_json(json_file, char_images):
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
    assets['button_click']     = pygame.mixer.Sound(resource_path("Assets/ButtonClicked.mp3"))
    assets['slide_in']         = pygame.mixer.Sound(resource_path("Assets/slide_in.mp3"))
    assets['skip_clicked']     = pygame.mixer.Sound(resource_path("Assets/skip_clicked.mp3"))
    assets['game_over']        = pygame.mixer.Sound(resource_path("Assets/GameOver.mp3"))
    assets['happy']            = pygame.mixer.Sound(resource_path("Assets/Happy.wav"))
    assets['sad'] = pygame.mixer.Sound(resource_path("Assets/Sad.wav"))

    assets['main_game_image']  = load_scaled_image("Assets/MainGame.png",  (SCREEN_WIDTH, SCREEN_HEIGHT))
    assets['main_menu_image']  = load_scaled_image("Assets/Menu.png",      (SCREEN_WIDTH, SCREEN_HEIGHT))

    assets['char_images'] = {}
    all_chars = load_chars_from_json("JSON/Characters.json", assets['char_images'])
    assets['boys_chars']  = [c for c in all_chars if c['Gender'] == 'Male']
    assets['girls_chars'] = [c for c in all_chars if c['Gender'] == 'Female']

    return assets

# ==============================================================================
# BUTTON / POPUP CREATION
# ==============================================================================
def create_buttons_and_popups():
    popups, buttons = load_popups_from_json("JSON/Popup.json")

    # Static buttons that aren't tied to any popup
    buttons['menu_start']   = Button("Buttons/StartGameButton.png", "Buttons/StartGameAnimation.png", (338, 385), (474, 109))
    buttons['menu_details'] = Button("Buttons/DetailsButton.png",   "Buttons/DetailsAnimation.png",   (338, 565), (474, 109))
    buttons['skip']         = Button("Buttons/Skip.png",            "Buttons/SkipAnimation.png",      (120, 655), (128, 130))

    return buttons, popups

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
        print(f"{BLUE}{BOLD}               Start a Scholar's Academic Life!")
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
# POPUP + BUTTON LOADING FROM JSON
# ==============================================================================
def load_popups_from_json(json_file="JSON/Popup.json"):
    with open(resource_path(json_file), "r") as f:
        data = json.load(f)

    popups  = {}
    buttons = {}

    for entry in data:
        name = entry["name"]
        w, h = entry["size"]

        popup = Popup(
            entry["image"],
            (w, h),
            target_y   = entry["target_y"],
            unclickable = entry["closable"]
        )
        popup.button_data = entry.get("buttons", [])
        popups[name] = popup

        for i, btn_data in enumerate(popup.button_data):
            key = f"{name}_{i}"
            buttons[key] = Button(
                btn_data["image"],
                btn_data["image_anim"],
                (0, 0),
                tuple(btn_data["size"])
            )
            buttons[key].role = btn_data["role"]
            buttons[key].stats = btn_data.get("stats", {})

    return popups, buttons

# ==============================================================================
# MENU SCENE — EVENT HANDLING
# ==============================================================================
def handle_menu_events(buttons, popups, game_state, event, blue_fade, assets):
    if blue_fade.active:
        return

    gender_popup  = popups['gender']
    details_popup = popups['details']

    if gender_popup.active:
        gender_popup.handle_event(event)

        for key, btn in buttons.items():
            if not key.startswith("gender_"):
                continue
            if btn.handle_event(event):
                assets['button_click'].play()
                if btn.role == "gender_boy":
                    game_state.gender = "boy"
                    game_state.selected_char = random.choice(assets['boys_chars'])
                    game_state.apply_char_stats(game_state.selected_char)  # ← add this
                elif btn.role == "gender_girl":
                    game_state.gender = "girl"
                    game_state.selected_char = random.choice(assets['girls_chars'])
                    game_state.apply_char_stats(game_state.selected_char)

                def switch_to_game():
                    popups['gender'].active = False  #
                    popups['gender'].state = None
                    game_state.scene = 'game'

                blue_fade.start(on_peak_callback=switch_to_game)

    elif details_popup.active:
        details_popup.handle_event(event)

    else:
        if buttons['menu_details'].handle_event(event):
            assets['button_click'].play()
            details_popup.open(sound=assets['slide_in'])

        if buttons['menu_start'].handle_event(event):
            assets['button_click'].play()
            gender_popup.open(sound=assets['slide_in'])

# ==============================================================================
# GAME SCENE — EVENT HANDLING
# ==============================================================================
STAT_INDEX = {
    "stress":        0,
    "happiness":     1,
    "grades":        2,
    "intelligence":  3,
}

def apply_stats(game_state, stats):
    for stat, value in stats.items():
        idx = STAT_INDEX.get(stat)
        if idx is not None:
            game_state.hp[idx] = max(0, min(100, game_state.hp[idx] + value))

def handle_game_events(buttons, popups, game_state, event, blue_fade, assets):
    if blue_fade.active:
        return

    any_popup_active = any(p.active for p in popups.values())
    if not any_popup_active:
        if buttons['skip'].handle_event(event):
            assets['skip_clicked'].play()
            print(f"\n{YELLOW}{BOLD}{'=' * 55}")
            print(f"                    Week {game_state.week} of 32 🗓️")
            print(f"{'=' * 55}{RESET}")
            game_state.week += 1
            if game_state.week > 32:
                blue_fade.start(on_peak_callback=lambda: setattr(game_state, 'scene', 'menu'))
                game_state.week = 0
            elif game_state.week % 4 == 0:
                chosen = random.choice([
                    'friend1',
                    'friend2',
                    'friend3',
                    'friend4',
                    'friend5',
                    'friend6',
                    'bully1',
                    'bully2',
                    'bully3',
                    'bully4'
                ])
                popups[chosen].open(sound=assets['slide_in'])
            else:
                popups['nce'].open(sound=assets['slide_in'])

    if popups['nce'].active:
        popups['nce'].handle_event(event)

        for key, btn in buttons.items():
            if not key.startswith("nce_"):
                continue
            if btn.handle_event(event):
                assets['button_click'].play()
                if btn.role == "nce_quiz":
                    idx = int(key.split("_")[1])
                    if idx == 0:
                        print(f"\n{BOLD}You studied hard all night just to take the NCE{RESET}")
                        print(" ")
                    elif idx == 1:
                        print(f"\n{BOLD}You did not study but still decided to take the NCE{RESET}")
                        print(" ")
                    apply_stats(game_state, btn.stats)
                    popups['nce'].close()
                    game_state.pending_quiz = True
                elif btn.role == "nce_close":
                    popups['nce'].active = False
                    popups['nce'].state = None
                    popups['gameover1'].open(sound=assets['game_over'])
                    print(f"\n{RED}{BOLD}{'=' * 55}")
                    print(f"                      Game Over!")
                    print(f"{'=' * 55}{RESET}\n")

    if popups['friend1'].active:
        popups['friend1'].handle_event(event)

        for key, btn in buttons.items():
            if not key.startswith("friend1_"):
                continue
            if btn.handle_event(event):
                assets['button_click'].play()
                apply_stats(game_state, btn.stats)
                if btn.role == "friends!":
                    idx = int(key.split("_")[1])
                    if idx == 0:
                        popups['friend1'].active = False
                        popups['friend1'].state = None
                        popups['friend1popup1'].open(sound=assets['happy'])
                        print(f"\n{BOLD}You decided to sit beside Hao Chang ")
                        print(f"You made a new friend! Hao Chang!{RESET}\n")
                        print(" ")

                    elif idx == 1:
                        popups['friend1'].active = False
                        popups['friend1'].state = None
                        popups['friend1popup2'].open(sound=assets['happy'])
                        print(f"\n{BOLD}You decided to compliment his thermos")
                        print(f"You made a new friend! Hao Chang!{RESET}\n")
                        print(" ")

                elif btn.role == "not friends":
                    popups['friend1'].active = False
                    popups['friend1'].state = None
                    popups['friend1popup3'].open(sound=assets['sad'])
                    print(f"\n{BOLD}You pretended to not notice him")
                    print(f"Awkward... he noticed you slightly looking at him before you walk away{RESET}\n")
                    print(" ")

    if popups['friend2'].active:
        popups['friend2'].handle_event(event)

        for key, btn in buttons.items():
            if not key.startswith("friend2_"):
                continue
            if btn.handle_event(event):
                assets['button_click'].play()
                apply_stats(game_state, btn.stats)
                if btn.role == "friends!":
                    popups['friend2'].active = False
                    popups['friend2'].state = None
                    popups['friend2popup1'].open(sound=assets['happy'])
                    print(f"\n{BOLD}You decided to just min your own business and just sit nearby him ")
                    print(f"You made a new friend! Juan Yuna!{RESET}\n")
                    print(" ")

                elif btn.role == "not friends":
                    popups['friend2'].active = False
                    popups['friend2'].state = None
                    if random.randint(0, 100) < 30:
                        popups['friend2popup2'].open(sound=assets['happy'])
                        print(f"\n{BOLD}You decided to ask what his drawing")
                        print(f"You made a new friend! Juan Yuna!{RESET}\n")
                        print(" ")

                    else:
                        popups['friend2popup3'].open(sound=assets['sad'])
                        print(f"\n{BOLD}You decided to ask what his drawing")
                        print(f"Awkward... he immediately shuts his notebook and scootched away{RESET}\n")
                        print(" ")

    if popups['friend3'].active:
        popups['friend3'].handle_event(event)

        for key, btn in buttons.items():
            if not key.startswith("friend3_"):
                continue
            if btn.handle_event(event):
                assets['button_click'].play()
                apply_stats(game_state, btn.stats)
                if btn.role == "friends!":
                    popups['friend3'].active = False
                    popups['friend3'].state = None
                    popups['f3p1'].open(sound=assets['happy'])
                    print(f"\n{BOLD}You got intruiged and asked Joze Lizal how he opened the locker ")
                    print(f"You made a new friend! Joze Lizal!{RESET}\n")
                    print(" ")

                elif btn.role == "not friends":
                    popups['friend3'].active = False
                    popups['friend3'].state = None
                    popups['f3p2'].open(sound=assets['sad'])
                    print(f"\n{BOLD}You ignored him and grabbed your stuff")
                    print(f"Awkward... He shrugs and does not bother you again{RESET}\n")
                    print(" ")

    if popups['friend4'].active:
        popups['friend4'].handle_event(event)

        for key, btn in buttons.items():
            if not key.startswith("friend4_"):
                continue
            if btn.handle_event(event):
                assets['button_click'].play()
                apply_stats(game_state, btn.stats)
                if btn.role == "friends!":
                    popups['friend4'].active = False
                    popups['friend4'].state = None
                    popups['f4p1'].open(sound=assets['happy'])
                    print(f"\n{BOLD}She decides your tolerable and you two nail the lab ")
                    print(f"You made a new friend! Li Tianxi!{RESET}\n")
                    print(" ")

                elif btn.role == "not friends":
                    popups['friend4'].active = False
                    popups['friend4'].state = None
                    popups['f4p2'].open(sound=assets['sad'])
                    print(f"\n{BOLD}You stared at her and the lab sheet in silence")
                    print(f"Awkward... She does most of the work in silence{RESET}\n")
                    print(" ")

    if popups['friend5'].active:
        popups['friend5'].handle_event(event)

        for key, btn in buttons.items():
            if not key.startswith("friend5_"):
                continue
            if btn.handle_event(event):
                assets['button_click'].play()
                apply_stats(game_state, btn.stats)
                if btn.role == "friends!":
                    popups['friend5'].active = False
                    popups['friend5'].state = None
                    popups['f5p1'].open(sound=assets['happy'])
                    print(f"\n{BOLD}You help her pick up the books and quiz eachother for an hour")
                    print(f"You made a new friend! Beth Sanchez!{RESET}\n")
                    print(" ")

                elif btn.role == "not friends":
                    popups['friend5'].active = False
                    popups['friend5'].state = None
                    popups['f5p2'].open(sound=assets['sad'])
                    print(f"\n{BOLD}You decided to ignore her and put your headphones back in")
                    print(f"Awkward... She struggles alone while you tune out{RESET}\n")
                    print(" ")

    if popups['friend6'].active:
        popups['friend6'].handle_event(event)

        for key, btn in buttons.items():
            if not key.startswith("friend6_"):
                continue
            if btn.handle_event(event):
                assets['button_click'].play()
                apply_stats(game_state, btn.stats)
                if btn.role == "friends!":
                    popups['friend6'].active = False
                    popups['friend6'].state = None
                    popups['f6p1'].open(sound=assets['happy'])
                    print(f"\n{BOLD}You two squeezed under the umbrella and spent the whole bus ride talking")
                    print(f"You made a new friend! Mai Nguyen!{RESET}\n")
                    print(" ")

                elif btn.role == "not friends":
                    popups['friend6'].active = False
                    popups['friend6'].state = None
                    popups['f6p2'].open(sound=assets['sad'])
                    print(f"\n{BOLD}You decided to stare at your phone awkwardly")
                    print(f"Awkward... You just watch her suffer while your scrolling{RESET}\n")
                    print(" ")

    if popups['bully1'].active:
        popups['bully1'].handle_event(event)

        for key, btn in buttons.items():
            if not key.startswith("bully1_"):
                continue
            if btn.handle_event(event):
                assets['button_click'].play()
                apply_stats(game_state, btn.stats)
                if btn.role == "not bullied":
                    popups['bully1'].active = False
                    popups['bully1'].state = None
                    popups['b1p1'].open(sound=assets['happy'])
                    print(f"\n{BOLD}You held your ground and did not fold")
                    print(f"You did not get bullied!!{RESET}\n")
                    print(" ")

                elif btn.role == "bullied!":
                    popups['bully1'].active = False
                    popups['bully1'].state = None
                    popups['b1p2'].open(sound=assets['sad'])
                    print(f"\n{BOLD}You scramble and they laughed harder")
                    print(f"You unfortunately got bullied by Alexander Graham{RESET}\n")
                    print(" ")

    if popups['bully2'].active:
        popups['bully2'].handle_event(event)

        for key, btn in buttons.items():
            if not key.startswith("bully2_"):
                continue
            if btn.handle_event(event):
                assets['button_click'].play()
                apply_stats(game_state, btn.stats)
                if btn.role == "not bullied":
                    popups['bully2'].active = False
                    popups['bully2'].state = None
                    popups['b2p1'].open(sound=assets['happy'])
                    print(f"\n{BOLD}You two squeezed under the umbrella and spent the whole bus ride talking")
                    print(f"You made a new friend! Mai Nguyen!{RESET}\n")
                    print(" ")

                elif btn.role == "bullied!":
                    popups['bully2'].active = False
                    popups['bully2'].state = None
                    popups['b2p2'].open(sound=assets['sad'])
                    print(f"\n{BOLD}You decided to stare at your phone awkwardly")
                    print(f"Awkward... You just watch her suffer while your scrolling{RESET}\n")
                    print(" ")

    if popups['bully3'].active:
        popups['bully3'].handle_event(event)

        for key, btn in buttons.items():
            if not key.startswith("bully3_"):
                continue
            if btn.handle_event(event):
                assets['button_click'].play()
                apply_stats(game_state, btn.stats)
                if btn.role == "not bullied":
                    popups['bully3'].active = False
                    popups['bully3'].state = None
                    popups['b3p2'].open(sound=assets['happy'])
                    print(f"\n{BOLD}You two squeezed under the umbrella and spent the whole bus ride talking")
                    print(f"You made a new friend! Mai Nguyen!{RESET}\n")
                    print(" ")

                elif btn.role == "bullied!":
                    popups['bully3'].active = False
                    popups['bully3'].state = None
                    popups['b3p1'].open(sound=assets['sad'])
                    print(f"\n{BOLD}You decided to stare at your phone awkwardly")
                    print(f"Awkward... You just watch her suffer while your scrolling{RESET}\n")
                    print(" ")

    if popups['bully4'].active:
        popups['bully4'].handle_event(event)

        for key, btn in buttons.items():
            if not key.startswith("bully4_"):
                continue
            if btn.handle_event(event):
                assets['button_click'].play()
                apply_stats(game_state, btn.stats)
                if btn.role == "not bullied":
                    popups['bully4'].active = False
                    popups['bully4'].state = None
                    popups['b4p3'].open(sound=assets['happy'])
                    print(f"\n{BOLD}You two squeezed under the umbrella and spent the whole bus ride talking")
                    print(f"You made a new friend! Mai Nguyen!{RESET}\n")
                    print(" ")

                elif btn.role == "bullied!":
                    popups['bully4'].active = False
                    popups['bully4'].state = None
                    if random.randint(0, 100) < 40:
                        popups['b4p2'].open(sound=assets['happy'])
                        print(f"\n{BOLD}You decided to ask what his drawing")
                        print(f"You made a new friend! Juan Yuna!{RESET}\n")
                        print(" ")

                    else:
                        popups['b4p1'].open(sound=assets['sad'])
                        print(f"\n{BOLD}You decided to ask what his drawing")
                        print(f"Awkward... he immediately shuts his notebook and scootched away{RESET}\n")
                        print(" ")

    for key in ('friend1popup1', 'friend1popup2', 'friend1popup3'): #<- Here
        popups[key].handle_event(event)
    for key in ('friend2popup1', 'friend2popup2', 'friend2popup3'):
        popups[key].handle_event(event)
    for key in ('f3p1', 'f3p2'):
        popups[key].handle_event(event)
    for key in ('f4p1', 'f4p2'):
        popups[key].handle_event(event)
    for key in ('f5p1', 'f5p2'):
        popups[key].handle_event(event)
    for key in ('f6p1', 'f6p2'):
        popups[key].handle_event(event)
    for key in ('b1p1', 'b1p2'):
        popups[key].handle_event(event)
    for key in ('b2p1', 'b2p2'):
        popups[key].handle_event(event)
    for key in ('b3p1', 'b3p2'):
        popups[key].handle_event(event)
    for key in ('b4p1', 'b4p2', 'b4p3'):
        popups[key].handle_event(event)

# ==============================================================================
# MENU SCENE — DRAWING
# ==============================================================================
def draw_menu(screen, buttons, popups):
    buttons['menu_start'].draw(screen)
    buttons['menu_details'].draw(screen)

    for popup in popups.values():
        popup.update()
        popup.draw(screen)

    if popups['gender'].active:
        popup_top = popups['gender'].rect.top
        for key, btn in buttons.items():
            if not key.startswith("gender_"):
                continue
            # find which button index this is to get offset_y
            idx = int(key.split("_")[1])
            offset_y = popups['gender'].button_data[idx]["offset_y"]
            btn.rect.center = (337, popup_top + offset_y)
            btn.draw(screen)
# ==============================================================================
# GAME SCENE — DRAWING
# ==============================================================================

def draw_health_bar(surface, hp_display, bar_x, bar_y, bar_w=250, bar_h=16, label="", invert=False):
    COLOR_HIGH = (144, 238, 144)
    COLOR_MID  = (255, 215, 0)
    COLOR_LOW  = (255, 153, 153)

    pct = max(0.0, min(100.0, hp_display))

    if invert:
        color = COLOR_LOW if pct >= 80 else COLOR_MID if pct >= 21 else COLOR_HIGH
    else:
        color = COLOR_HIGH if pct >= 80 else COLOR_MID if pct >= 21 else COLOR_LOW

    if label:
        font_lbl = pygame.font.SysFont("Segoe UI", 12, bold=True)
        lbl = font_lbl.render(label, True, (255, 255, 255))
        surface.blit(lbl, (bar_x - lbl.get_width() - 8, bar_y + bar_h // 2 - lbl.get_height() // 2))

    pygame.draw.rect(surface, (60, 60, 70), (bar_x, bar_y, bar_w, bar_h), border_radius=6)
    fill_w = int(bar_w * pct / 100)
    if fill_w > 0:
        pygame.draw.rect(surface, color, (bar_x, bar_y, fill_w, bar_h), border_radius=6)
    pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=6)

    font = pygame.font.SysFont("Segoe UI", 12, bold=True)
    txt  = font.render(f"{int(round(pct))}%", True, (255, 255, 255))
    surface.blit(txt, txt.get_rect(center=(bar_x + bar_w // 2, bar_y + bar_h // 2)))

def draw_game(screen, assets, game_state, buttons, popups):
    screen.blit(assets['main_game_image'], (0, 0))

    if game_state.selected_char:
        face_img = assets['char_images'][game_state.selected_char['Appearance']]
        screen.blit(face_img, (-7, -1))

    BAR_X       = 290
    BAR_START_Y = 377
    BAR_GAP     = 51
    BAR_W       = 310
    BAR_H       = 25

    for i in range(4):
        diff = game_state.hp[i] - game_state.hp_display[i]
        game_state.hp_display[i] += diff * 0.12
        draw_health_bar(screen, game_state.hp_display[i],
        bar_x=BAR_X,
        bar_y=BAR_START_Y + i * BAR_GAP,
        bar_w=BAR_W,
        bar_h=BAR_H,
        invert=(i == 1)
        )

    buttons['skip'].draw(screen)

    popups['nce'].update()
    popups['nce'].draw(screen)
    popups['friend1'].update()
    popups['friend1'].draw(screen)
    popups['friend2'].update()
    popups['friend2'].draw(screen)
    popups['friend3'].update()
    popups['friend3'].draw(screen)
    popups['friend4'].update()
    popups['friend4'].draw(screen)
    popups['friend5'].update()
    popups['friend5'].draw(screen)
    popups['friend6'].update()
    popups['friend6'].draw(screen)
    popups['bully1'].update()
    popups['bully1'].draw(screen)
    popups['bully2'].update()
    popups['bully2'].draw(screen)
    popups['bully3'].update()
    popups['bully3'].draw(screen)
    popups['bully4'].update()
    popups['bully4'].draw(screen)

    if popups['nce'].active:
        popup_top = popups['nce'].rect.top
        for key, btn in buttons.items():
            if not key.startswith("nce_"):
                continue
            idx = int(key.split("_")[1])
            offset_y = popups['nce'].button_data[idx]["offset_y"]
            btn.rect.center = (349, popup_top + offset_y)
            btn.draw(screen)

    if popups['friend1'].active:
        popup_top = popups['friend1'].rect.top
        for key, btn in buttons.items():
            if not key.startswith("friend1_"):
                continue
            idx = int(key.split("_")[1])
            offset_y = popups['friend1'].button_data[idx]["offset_y"]
            btn.rect.center = (349, popup_top + offset_y)
            btn.draw(screen)

    if popups['friend2'].active:
        popup_top = popups['friend2'].rect.top
        for key, btn in buttons.items():
            if not key.startswith("friend2_"):
                continue
            idx = int(key.split("_")[1])
            offset_y = popups['friend2'].button_data[idx]["offset_y"]
            btn.rect.center = (349, popup_top + offset_y)
            btn.draw(screen)

    if popups['friend3'].active:
        popup_top = popups['friend3'].rect.top
        for key, btn in buttons.items():
            if not key.startswith("friend3_"):
                continue
            idx = int(key.split("_")[1])
            offset_y = popups['friend3'].button_data[idx]["offset_y"]
            btn.rect.center = (349, popup_top + offset_y)
            btn.draw(screen)

    if popups['friend4'].active:
        popup_top = popups['friend4'].rect.top
        for key, btn in buttons.items():
            if not key.startswith("friend4_"):
                continue
            idx = int(key.split("_")[1])
            offset_y = popups['friend4'].button_data[idx]["offset_y"]
            btn.rect.center = (349, popup_top + offset_y)
            btn.draw(screen)

    if popups['friend5'].active:
        popup_top = popups['friend5'].rect.top
        for key, btn in buttons.items():
            if not key.startswith("friend5_"):
                continue
            idx = int(key.split("_")[1])
            offset_y = popups['friend5'].button_data[idx]["offset_y"]
            btn.rect.center = (349, popup_top + offset_y)
            btn.draw(screen)

    if popups['friend6'].active:
        popup_top = popups['friend6'].rect.top
        for key, btn in buttons.items():
            if not key.startswith("friend6_"):
                continue
            idx = int(key.split("_")[1])
            offset_y = popups['friend6'].button_data[idx]["offset_y"]
            btn.rect.center = (349, popup_top + offset_y)
            btn.draw(screen)

    if popups['bully1'].active:
        popup_top = popups['bully1'].rect.top
        for key, btn in buttons.items():
            if not key.startswith("bully1_"):
                continue
            idx = int(key.split("_")[1])
            offset_y = popups['bully1'].button_data[idx]["offset_y"]
            btn.rect.center = (349, popup_top + offset_y)
            btn.draw(screen)

    if popups['bully2'].active:
        popup_top = popups['bully2'].rect.top
        for key, btn in buttons.items():
            if not key.startswith("bully2_"):
                continue
            idx = int(key.split("_")[1])
            offset_y = popups['bully2'].button_data[idx]["offset_y"]
            btn.rect.center = (349, popup_top + offset_y)
            btn.draw(screen)

    if popups['bully3'].active:
        popup_top = popups['bully3'].rect.top
        for key, btn in buttons.items():
            if not key.startswith("bully3_"):
                continue
            idx = int(key.split("_")[1])
            offset_y = popups['bully3'].button_data[idx]["offset_y"]
            btn.rect.center = (349, popup_top + offset_y)
            btn.draw(screen)

    if popups['bully4'].active:
        popup_top = popups['bully4'].rect.top
        for key, btn in buttons.items():
            if not key.startswith("bully4_"):
                continue
            idx = int(key.split("_")[1])
            offset_y = popups['bully4'].button_data[idx]["offset_y"]
            btn.rect.center = (349, popup_top + offset_y)
            btn.draw(screen)

    popups['gameover1'].update()
    popups['gameover1'].draw(screen)
    popups['gameover2'].update()
    popups['gameover2'].draw(screen)
    popups['friend1popup1'].update()
    popups['friend1popup1'].draw(screen)
    popups['friend1popup2'].update()
    popups['friend1popup2'].draw(screen)
    popups['friend1popup3'].update()
    popups['friend1popup3'].draw(screen)
    popups['friend2popup1'].update()
    popups['friend2popup1'].draw(screen)
    popups['friend2popup2'].update()
    popups['friend2popup2'].draw(screen)
    popups['friend2popup3'].update()
    popups['friend2popup3'].draw(screen)
    popups['f3p1'].update()
    popups['f3p1'].draw(screen)
    popups['f3p2'].update()
    popups['f3p2'].draw(screen)
    popups['f4p1'].update()
    popups['f4p1'].draw(screen)
    popups['f4p2'].update()
    popups['f4p2'].draw(screen)
    popups['f5p1'].update()
    popups['f5p1'].draw(screen)
    popups['f5p2'].update()
    popups['f5p2'].draw(screen)
    popups['f6p1'].update()
    popups['f6p1'].draw(screen)
    popups['f6p2'].update()
    popups['f6p2'].draw(screen)
    popups['b1p1'].update()
    popups['b1p1'].draw(screen)
    popups['b1p2'].update()
    popups['b1p2'].draw(screen)
    popups['b2p1'].update()
    popups['b2p1'].draw(screen)
    popups['b2p2'].update()
    popups['b2p2'].draw(screen)
    popups['b3p1'].update()
    popups['b3p1'].draw(screen)
    popups['b3p2'].update()
    popups['b3p2'].draw(screen)
    popups['b4p1'].update()
    popups['b4p1'].draw(screen)
    popups['b4p2'].update()
    popups['b4p2'].draw(screen)
    popups['b4p3'].update()
    popups['b4p3'].draw(screen)

# ==============================================================================
# MAIN LOOP
# ==============================================================================
def main():
    assets          = load_assets()
    buttons, popups = create_buttons_and_popups()
    game_state      = GameState()
    blue_fade       = Fade()

    while game_state.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_state.running = False

            if not game_state.playing_video and game_state.scene == "menu":
                handle_menu_events(buttons, popups, game_state, event, blue_fade, assets)

            elif not game_state.playing_video and game_state.scene == "game":
                handle_game_events(buttons, popups, game_state, event, blue_fade, assets)

        if game_state.pending_quiz:
            game_state.pending_quiz = False
            score = run_nce_quiz()
            if score < 8:
                print(f"\n{RED}{BOLD}{'=' * 55}")
                print(f"    Game Over!")
                print(f"{'=' * 55}{RESET}\n")
                popups['gameover2'].open(sound=assets['game_over'])

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