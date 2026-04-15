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
import pygame, os, sys, json, random, math
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
def run_nce_quiz(json_file="JSON/NCE_Question.json"):
    with open(resource_path(json_file), "r") as f:
        all_questions = json.load(f)

    subjects = {}
    for q in all_questions:
        subj = q["Subject"]
        if subj not in subjects:
            subjects[subj] = []
        subjects[subj].append(q)

    subject_order = list(subjects.keys())
    random.shuffle(subject_order)
    for subj in subject_order:
        random.shuffle(subjects[subj])

    score = 0
    total = sum(len(subjects[s]) for s in subject_order)
    question_num = 1

    for subj in subject_order:
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

    print(f"\n{BOLD}NCE Complete!  Score: {score}/{total}")
    if score >= 8:
        print(f"Nice work! Keep it up! 🌟📚✨")
    else:
        print(f"Yikes... better hit the books! 😬📖💀")
        print(f"You got {7 - score + 1} more wrong than passing... 😅{RESET}\n")
    return score

# ==============================================================================
# MINIGAME — load configs from JSON
# ==============================================================================
with open(resource_path("JSON/Minigame.json"), "r") as f:
    _mg_json = json.load(f)

# Convert color lists [r,g,b] back to tuples so pygame is happy
MINIGAME_BAR = _mg_json["bar"]
MINIGAME_CONFIGS = {
    name: {
        **cfg,
        "needle_color":  tuple(cfg["needle_color"]),
        "green_color":   tuple(cfg["green_color"]),
        "track_color":   tuple(cfg["track_color"]),
        "danger_color":  tuple(cfg["danger_color"]),
    }
    for name, cfg in _mg_json["minigames"].items()
}

class MinigameState:

    TRACK_LEFT   = MINIGAME_BAR["track_left"]
    TRACK_RIGHT  = MINIGAME_BAR["track_right"]
    TRACK_Y      = MINIGAME_BAR["track_y"]
    TRACK_H      = MINIGAME_BAR["track_h"]
    DANGER_W     = MINIGAME_BAR["danger_zone_w"]
    TRACK_W      = TRACK_RIGHT - TRACK_LEFT
    TOTAL_ROUNDS = 3
    FLASH_DURATION = 90

    def __init__(self, minigame_name):
        cfg = MINIGAME_CONFIGS.get(minigame_name, MINIGAME_CONFIGS["minigame1"])
        self.cfg            = cfg
        self.name           = minigame_name

        self.needle_x       = float(self.TRACK_LEFT)
        self.direction      = 1
        self.current_speed  = cfg["speed"]

        self.round          = 0
        self.wins           = 0
        self.done           = False
        self.passed         = False

        self.green_left     = 0
        self.green_right    = 0
        self._place_green()

        self.flash_timer    = 0
        self.flash_text     = ""
        self.flash_color    = (255, 255, 255)

        self.particles      = []

        self._font_big      = pygame.font.SysFont("consolas", 26, bold=True)
        self._font_small    = pygame.font.SysFont("consolas", 16, bold=True)
        self._font_round    = pygame.font.SysFont("consolas", 18, bold=True)

    def _place_green(self):
        gw = int(self.TRACK_W * self.cfg["green_w_frac"])
        max_left = self.TRACK_RIGHT - gw - 20
        self.green_left  = random.randint(self.TRACK_LEFT + 20, max_left)
        self.green_right = self.green_left + gw

    def _lerp_color(self, c1, c2, t):
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

    def _burst(self, x, y, color):
        for _ in range(18):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(2, 6)
            self.particles.append({
                "x": x, "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed - 2,
                "color": color,
                "life": 1.0,
                "size": random.randint(3, 7),
            })

    def hit(self):
        if self.done or self.flash_timer > 0:
            return

        nx = self.needle_x
        if self.green_left <= nx <= self.green_right:
            self.wins += 1
            self.flash_text  = f"HIT!  ({self.wins}/{self.TOTAL_ROUNDS})"
            self.flash_color = self.cfg["green_color"]
            self._burst(int(nx), self.TRACK_Y, self.cfg["green_color"])
        else:
            self.flash_text  = "MISS!"
            self.flash_color = (230, 60, 60)
            self._burst(int(nx), self.TRACK_Y, (230, 60, 60))

        self.flash_timer = self.FLASH_DURATION
        self.round += 1

        if self.round >= self.TOTAL_ROUNDS:
            self.done   = True
            self.passed = (self.wins == self.TOTAL_ROUNDS)

    def update(self):
        if self.done:
            return

        if self.flash_timer > 0:
            self.flash_timer -= 1
            if self.flash_timer == 0 and not self.done:
                # Advance to next round
                self._place_green()
                self.current_speed += self.cfg["speed_increment"]
                self.needle_x = float(self.TRACK_LEFT)
                self.direction = 1
        else:
            self.needle_x += self.current_speed * self.direction
            if self.needle_x >= self.TRACK_RIGHT:
                self.needle_x = float(self.TRACK_RIGHT)
                self.direction = -1
            elif self.needle_x <= self.TRACK_LEFT:
                self.needle_x = float(self.TRACK_LEFT)
                self.direction = 1

        for p in self.particles:
            p["x"]    += p["vx"]
            p["y"]    += p["vy"]
            p["vy"]   += 0.25
            p["life"] -= 0.04
        self.particles = [p for p in self.particles if p["life"] > 0]

    def draw(self, surface):
        cfg = self.cfg
        TL  = self.TRACK_LEFT
        TR  = self.TRACK_RIGHT
        TY  = self.TRACK_Y
        TH  = self.TRACK_H
        TW  = self.TRACK_W

        top = TY - TH // 2

        for i in range(self.TOTAL_ROUNDS):
            cx = SCREEN_WIDTH // 2 + (i - self.TOTAL_ROUNDS // 2) * 28 + 14
            filled = i < self.round
            pygame.draw.circle(surface, cfg["green_color"] if filled else (80, 80, 100), (cx, top - 22), 8)
            if filled:
                pygame.draw.circle(surface, (255, 255, 255), (cx, top - 22), 4)

        # Round label
        rnd_txt = self._font_round.render(
            f"Round {min(self.round + 1, self.TOTAL_ROUNDS)}/{self.TOTAL_ROUNDS}",
            True, (200, 200, 220))
        surface.blit(rnd_txt, (TL, top - 32))

        shadow_rect = pygame.Rect(TL + 3, top + 5, TW, TH)
        pygame.draw.rect(surface, (10, 10, 20), shadow_rect, border_radius=10)

        track_rect = pygame.Rect(TL, top, TW, TH)
        pygame.draw.rect(surface, cfg["track_color"], track_rect, border_radius=10)

        dw = 25
        pygame.draw.rect(surface, cfg["danger_color"], pygame.Rect(TL, top, dw, TH), border_radius=10)
        pygame.draw.rect(surface, cfg["danger_color"], pygame.Rect(TR - dw, top, dw, TH), border_radius=10)

        gw   = self.green_right - self.green_left
        gz   = pygame.Rect(self.green_left, top, gw, TH)
        pygame.draw.rect(surface, cfg["green_color"], gz, border_radius=7)

        hl = pygame.Rect(self.green_left + 4, top + 4, gw - 8, 8)
        bright = self._lerp_color(cfg["green_color"], (255, 255, 255), 0.5)
        pygame.draw.rect(surface, bright, hl, border_radius=3)

        gc = (self.green_left + self.green_right) // 2
        pygame.draw.line(surface, (255, 255, 255), (gc, top + 3), (gc, top + TH - 3), 2)

        pygame.draw.rect(surface, (80, 80, 110), track_rect, 2, border_radius=10)

        if self.flash_timer == 0 or not self.done:
            nx = int(self.needle_x)
            pygame.draw.line(surface, (0, 0, 0), (nx + 2, top - 12), (nx + 2, top + TH + 12), 4)
            pygame.draw.line(surface, cfg["needle_color"], (nx, top - 12), (nx, top + TH + 12), 3)
            pygame.draw.circle(surface, cfg["needle_color"], (nx, top - 12), 5)
            pygame.draw.circle(surface, cfg["needle_color"], (nx, top + TH + 12), 5)
            pygame.draw.circle(surface, (255, 255, 255), (nx, top - 12), 2)
            pygame.draw.circle(surface, (255, 255, 255), (nx, top + TH + 12), 2)

        if self.flash_timer > 0:
            t   = self.flash_timer / self.FLASH_DURATION
            sz  = int(20 + 10 * (1 - abs(t - 0.5) * 2))
            fnt = pygame.font.SysFont("consolas", sz, bold=True)
            txt = fnt.render(self.flash_text, True, self.flash_color)
            shadow = fnt.render(self.flash_text, True, (0, 0, 0))
            cx = SCREEN_WIDTH // 2
            ty = top + TH + 18
            surface.blit(shadow, (cx - txt.get_width() // 2 + 2, ty + 2))
            surface.blit(txt,    (cx - txt.get_width() // 2,     ty))

        if self.done:
            msg = "ALL HIT! ✓" if self.passed else f"FAILED ({self.wins}/3)"
            col = cfg["green_color"] if self.passed else (230, 60, 60)
            txt = self._font_big.render(msg, True, col)
            shd = self._font_big.render(msg, True, (0, 0, 0))
            cx  = SCREEN_WIDTH // 2
            ty  = top + TH + 20
            surface.blit(shd, (cx - txt.get_width() // 2 + 2, ty + 2))
            surface.blit(txt, (cx - txt.get_width() // 2,     ty))

        for p in self.particles:
            alpha = max(0, p["life"])
            col   = self._lerp_color(p["color"], (0, 0, 0), 1 - alpha)
            r     = max(1, int(p["size"] * alpha))
            pygame.draw.circle(surface, col, (int(p["x"]), int(p["y"])), r)


        lbl = self._font_small.render(f"[ {cfg['label']} MINIGAME ]", True, (160, 160, 200))
        surface.blit(lbl, (TL, top - 52))

# ==============================================================================
# POPUP
# ==============================================================================
class Popup:
    OFFSCREEN_Y   = -400
    SLIDE_SPEED   = 35
    BOB_STRENGTH  = -8
    GRAVITY       = 1.2
    BOB_DAMPEN    = 0.55
    BOB_STOP      = 1.5
    SLIDE_OUT_SPD = 22

    def __init__(self, image_path, size, target_y, unclickable=True):
        self.image      = load_scaled_image(image_path, size)
        self.rect       = self.image.get_rect(centerx=SCREEN_WIDTH // 2, top=self.OFFSCREEN_Y)
        self.target_y   = target_y
        self.unclickable = unclickable
        self.state      = None
        self.vel        = 0.0
        self.active     = False
        self.minigame   = None   # MinigameState or None

    def open(self, sound=None):
        self.rect.top = self.OFFSCREEN_Y
        self.vel      = self.SLIDE_SPEED
        self.state    = 'slide_in'
        self.active   = True
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
            if self.minigame and self.state is None:
                pass  # minigame starts updating once settled

        elif self.state == 'slide_out':
            self.rect.top += self.vel
            if self.rect.top > SCREEN_HEIGHT:
                self.active   = False
                self.state    = None
                self.minigame = None

        # Update embedded minigame
        if self.minigame and self.state is None:
            self.minigame.update()

    def draw(self, surface):
        if not self.active:
            return
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        surface.blit(self.image, self.rect)
        if self.minigame and self.state is None:
            self.minigame.draw(surface)

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
            was_holding        = self.is_holding
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
        self.overlay     = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.overlay.fill((15, 58, 78))
        self.alpha       = 0
        self.state       = None
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
        self.running        = True
        self.playing_video  = True
        self.week           = 0
        self.scene          = "menu"
        self.gender         = None
        self.selected_char  = None
        self.pending_quiz   = False
        self.hp             = [0, 0, 0, 0]
        self.hp_display     = [0.0, 0.0, 0.0, 0.0]
        # Minigame result pending (set after minigame popup closes)
        self.pending_mg_result = None   # None | (popup_name, passed)

    def apply_char_stats(self, char):
        self.hp = [
            char.get("starting_stress",       20),
            char.get("starting_happiness",    40),
            char.get("starting_grades",       30),
            char.get("starting_intelligence",  0),
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
    assets['intro_video']     = MediaPlayer(resource_path("Assets/GameIntro.mov"))
    assets['button_click']    = pygame.mixer.Sound(resource_path("Assets/ButtonClicked.mp3"))
    assets['slide_in']        = pygame.mixer.Sound(resource_path("Assets/slide_in.mp3"))
    assets['skip_clicked']    = pygame.mixer.Sound(resource_path("Assets/skip_clicked.mp3"))
    assets['game_over']       = pygame.mixer.Sound(resource_path("Assets/GameOver.mp3"))
    assets['happy']           = pygame.mixer.Sound(resource_path("Assets/Happy.wav"))
    assets['sad']             = pygame.mixer.Sound(resource_path("Assets/Sad.wav"))

    assets['main_game_image'] = load_scaled_image("Assets/MainGame.png",  (SCREEN_WIDTH, SCREEN_HEIGHT))
    assets['main_menu_image'] = load_scaled_image("Assets/Menu.png",      (SCREEN_WIDTH, SCREEN_HEIGHT))

    assets['char_images']     = {}
    all_chars                 = load_chars_from_json("JSON/Characters.json", assets['char_images'])
    assets['boys_chars']      = [c for c in all_chars if c['Gender'] == 'Male']
    assets['girls_chars']     = [c for c in all_chars if c['Gender'] == 'Female']

    return assets

# ==============================================================================
# BUTTON / POPUP CREATION
# ==============================================================================
def create_buttons_and_popups():
    popups, buttons = load_popups_from_json("JSON/Popup.json")

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
            target_y    = entry["target_y"],
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
            buttons[key].role  = btn_data["role"]
            buttons[key].stats = btn_data.get("stats", {})

    return popups, buttons

# ==============================================================================
# MINIGAME NAMES (all 8)
# ==============================================================================
ALL_MINIGAMES = [f"minigame{i}" for i in range(1, 9)]

def is_minigame_popup(name):
    return name in ALL_MINIGAMES

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
                    game_state.apply_char_stats(game_state.selected_char)
                elif btn.role == "gender_girl":
                    game_state.gender = "girl"
                    game_state.selected_char = random.choice(assets['girls_chars'])
                    game_state.apply_char_stats(game_state.selected_char)

                def switch_to_game():
                    popups['gender'].active = False
                    popups['gender'].state  = None
                    game_state.scene        = 'game'

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
    "stress":       0,
    "happiness":    1,
    "grades":       2,
    "intelligence": 3,
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
            elif game_state.week % 4 == 2:
                chosen = random.choice([
                    'friend1', 'friend2', 'friend3', 'friend4', 'friend5', 'friend6',
                    'bully1',  'bully2',  'bully3',  'bully4',
                ])
                popups[chosen].open(sound=assets['slide_in'])
            elif game_state.week % 4 == 1:
                # Minigame week
                chosen_mg = random.choice(ALL_MINIGAMES)
                popups[chosen_mg].open(sound=assets['slide_in'])
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
                        print(f"\n{BOLD}You studied hard all night just to take the NCE{RESET}\n")
                    elif idx == 1:
                        print(f"\n{BOLD}You did not study but still decided to take the NCE{RESET}\n")
                    apply_stats(game_state, btn.stats)
                    popups['nce'].close()
                    game_state.pending_quiz = True
                elif btn.role == "nce_close":
                    popups['nce'].active = False
                    popups['nce'].state  = None
                    popups['gameover1'].open(sound=assets['game_over'])
                    print(f"\n{RED}{BOLD}{'=' * 55}")
                    print(f"                      Game Over!")
                    print(f"{'=' * 55}{RESET}\n")

    for mg_name in ALL_MINIGAMES:
        popup = popups[mg_name]
        if not popup.active:
            continue

        if popup.state is None and popup.minigame is None:
            popup.minigame = MinigameState(mg_name)

        mg = popup.minigame
        key = f"{mg_name}_0"
        if key in buttons:
            btn = buttons[key]
            if popup.button_data:
                offset_y = popup.button_data[0]["offset_y"]
                btn.rect.center = (349, popup.rect.top + offset_y)
            btn.draw(screen)

            if mg and not mg.done:
                if btn.handle_event(event):
                    assets['button_click'].play()
                    mg.hit()
            elif mg and mg.done:
                if btn.handle_event(event):
                    assets['button_click'].play()
                    passed = mg.passed
                    popup.active   = False
                    popup.state    = None
                    popup.minigame = None
                    result_popup = f"{mg_name[2:]}p1" if passed else f"{mg_name[2:]}p2"
                    rkey = f"mg{mg_name[-1]}p{'1' if passed else '2'}"
                    sound = assets['happy'] if passed else assets['sad']
                    if rkey in popups:
                        popups[rkey].open(sound=sound)
                    print(f"\n{BOLD}Minigame {mg_name[-1]}: {'PASSED ✓' if passed else 'FAILED ✗'}{RESET}\n")

    for key in ('friend1popup1', 'friend1popup2', 'friend1popup3',
                'friend2popup1', 'friend2popup2', 'friend2popup3',
                'f3p1', 'f3p2', 'f4p1', 'f4p2', 'f5p1', 'f5p2', 'f6p1', 'f6p2',
                'b1p1', 'b1p2', 'b2p1', 'b2p2', 'b3p1', 'b3p2',
                'b4p1', 'b4p2', 'b4p3',
                'mg1p1', 'mg1p2', 'mg2p1', 'mg2p2', 'mg3p1', 'mg3p2',
                'mg4p1', 'mg4p2', 'mg5p1', 'mg5p2', 'mg6p1', 'mg6p2',
                'mg7p1', 'mg7p2', 'mg8p1', 'mg8p2'):
        if key in popups:
            popups[key].handle_event(event)

with open(resource_path("JSON/Lore.json"), "r") as f:
    EVENT_DATA = json.load(f)

def trigger_event_popup(event_id, buttons, popups, game_state, event, assets):
    data   = EVENT_DATA[event_id]
    popup  = popups[data["popup"]]

    if not popup.active:
        return

    popup.handle_event(event)
    prefix = data["buttons_"]
    for key, btn in buttons.items():
        if not key.startswith(prefix):
            continue
        if not btn.handle_event(event):
            continue

        assets['button_click'].play()
        apply_stats(game_state, btn.stats)
        role    = btn.role
        options = data["choices"].get(role)
        if not options:
            continue

        roll    = random.randint(0, 99)
        cumul   = 0
        chosen  = options[-1]
        for option in options:
            cumul += option["prob"]
            if roll < cumul:
                chosen = option
                break

        popup.active = False
        popup.state  = None
        popups[chosen["result"]].open(sound=assets[chosen["sound"]])
        print(f"\n{BOLD}{chosen['log']}{RESET}\n")

def _handle_friend_bully(buttons, popups, game_state, event, assets):
    for event_id in EVENT_DATA:
        trigger_event_popup(event_id, buttons, popups, game_state, event, assets)

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
            idx      = int(key.split("_")[1])
            offset_y = popups['gender'].button_data[idx]["offset_y"]
            btn.rect.center = (337, popup_top + offset_y)
            btn.draw(screen)

# ==============================================================================
# GAME SCENE — DRAWING
# ==============================================================================
def draw_health_bar(surface, hp_display, bar_x, bar_y, bar_w=250, bar_h=16, label="", invert=False):
    COLOR_HIGH = (144, 238, 144)
    COLOR_MID  = (255, 215,   0)
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
                        bar_x=BAR_X, bar_y=BAR_START_Y + i * BAR_GAP,
                        bar_w=BAR_W, bar_h=BAR_H,
                        invert=(i == 1))

    buttons['skip'].draw(screen)
    regular_popups = [
        'nce',
        'friend1', 'friend2', 'friend3', 'friend4', 'friend5', 'friend6',
        'bully1',  'bully2',  'bully3',  'bully4',
        'gameover1', 'gameover2',
        'friend1popup1', 'friend1popup2', 'friend1popup3',
        'friend2popup1', 'friend2popup2', 'friend2popup3',
        'f3p1', 'f3p2', 'f4p1', 'f4p2', 'f5p1', 'f5p2', 'f6p1', 'f6p2',
        'b1p1', 'b1p2', 'b2p1', 'b2p2', 'b3p1', 'b3p2', 'b4p1', 'b4p2', 'b4p3',
        'mg1p1', 'mg1p2', 'mg2p1', 'mg2p2', 'mg3p1', 'mg3p2',
        'mg4p1', 'mg4p2', 'mg5p1', 'mg5p2', 'mg6p1', 'mg6p2',
        'mg7p1', 'mg7p2', 'mg8p1', 'mg8p2',
    ]

    for pname in regular_popups:
        if pname not in popups:
            continue
        popup = popups[pname]
        popup.update()
        popup.draw(screen)

        prefix = pname + "_"
        if popup.active:
            popup_top = popup.rect.top
            for key, btn in buttons.items():
                if not key.startswith(prefix):
                    continue
                idx      = int(key.split("_")[-1])
                if idx < len(popup.button_data):
                    offset_y = popup.button_data[idx]["offset_y"]
                    btn.rect.center = (349, popup_top + offset_y)
                btn.draw(screen)

    for mg_name in ALL_MINIGAMES:
        if mg_name not in popups:
            continue
        popup = popups[mg_name]
        popup.update()
        popup.draw(screen)

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