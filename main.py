"""
╔══════════════════════════════════════════════════════╗
║                  B I T H I G H  🎮                   ║
║  a game about surviving high school. good luck lol   ║
╠══════════════════════════════════════════════════════╣
║  MEMBERS:                                            ║
║    ✏  Bocalan, Rachel                                ║
║    ✏  Carpizo, Eunice                                ║
║    ✏  Tudayan, Matt Jhardy                           ║
╚══════════════════════════════════════════════════════╝
"""

# ============================================================
#  [1]  IMPORTS & INITIALIZATION
#       all the stuff python needs for the game to work
# ============================================================
import pygame, os, sys, json, random, math
from ffpyplayer.player import MediaPlayer      # <- needed for the intro video!!
                                               #    install: pip install ffpyplayer

pygame.init()
pygame.display.set_caption("BitHigh")
pygame.display.set_icon(pygame.image.load("Assets/BitHighIcon.png"))

SCREEN_WIDTH  = 686
SCREEN_HEIGHT = 768
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock  = pygame.time.Clock()

# console colors for the NCE quiz output (ANSI codes)
RED, GREEN, YELLOW = "\033[31m", "\033[32m", "\033[33m"
BLUE, MAGENTA, CYAN = "\033[34m", "\033[35m", "\033[36m"
RESET = "\033[0m"
BOLD  = "\033[1m"


# ============================================================
#  [2]  UTILITY FUNCTIONS
# ============================================================
def resource_path(relative):
    """
    finds the right folder whether we're running the .py
    or a compiled .exe (pyinstaller changes where files live)
    """
    base = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
    return os.path.join(base, relative)


def load_scaled_image(path, size):
    """load an image from disk and immediately scale it — saves us two lines every time"""
    return pygame.transform.scale(pygame.image.load(resource_path(path)), size)


# ============================================================
#  [3]  NCE QUIZ
#       runs in the terminal (not in pygame) during the game
#       questions come from JSON/NCE.json
#
#       scoring:  8+ correct  →  pass  ✓
#                 7 or less   →  game over  ✗
# ============================================================
# which quiz role runs on which game week
MONTH_QUIZ_SCHEDULE = {
    1: "Math Quiz",
    2: "Math Long Test",
    3: "Science Quiz",
    4: "Science Long Test",
    5: "English Quiz",
    6: "English Long Test",
    7: "Mix Quiz",
    8: "Mix Long Test",
}

QUIZ_PASSED = {
    "NCE":               8,
    "Math Quiz":         6,
    "Math Long Test":    6,
    "Science Quiz":      6,
    "Science Long Test": 6,
    "English Quiz":      6,
    "English Long Test": 6,
    "Mix Quiz":          6,
    "Mix Long Test":     8,
}

# maps each quiz role to the JSON file that holds its questions.
# if you split questions into separate files later, update the paths here.
QUIZ_JSON_MAP = {
    "NCE":               "JSON/NCE.json",
    "Math Quiz":         "JSON/NCE.json",
    "Math Long Test":    "JSON/NCE.json",
    "Science Quiz":      "JSON/NCE.json",
    "Science Long Test": "JSON/NCE.json",
    "English Quiz":      "JSON/NCE.json",
    "English Long Test": "JSON/NCE.json",
    "Mix Quiz":          "JSON/NCE.json",
    "Mix Long Test":     "JSON/NCE.json",
}

def run_nce_quiz(json_file="JSON/NCE.json", role="NCE"):
    print(f"\n{MAGENTA}{BOLD}{'=' * 55}")
    print(f"           📋 {role.upper()} 📋")
    print(f"{'=' * 55}{RESET}")

    with open(resource_path(json_file), "r") as f:
        all_questions = json.load(f)

    # filter questions by the requested role
    role_questions = [q for q in all_questions if q["Role"] == role]

    # group by subject so they appear in subject blocks
    subjects = {}
    for q in role_questions:
        subj = q["Subject"]
        if subj not in subjects:
            subjects[subj] = []
        subjects[subj].append(q)

    subject_order = list(subjects.keys())
    random.shuffle(subject_order)
    for subj in subject_order:
        random.shuffle(subjects[subj])

    score        = 0
    total        = sum(len(subjects[s]) for s in subject_order)
    pass_score   = QUIZ_PASSED.get(role, 8)
    question_num = 1

    for subj in subject_order:
        print(f"\n{CYAN}{BOLD}{'-'*55}")
        print(f"  {subj}!!!")
        print(f"{'-'*55}{RESET}")

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

    print(f"\n{BOLD}{role} Complete!  Score: {score}/{total}  (Pass: {pass_score}+)")
    if score >= pass_score:
        print(f"Nice work! Keep it up! 🌟📚✨")
    else:
        print(f"Yikes... better hit the books! 😬📖💀")
        print(f"You need {pass_score} to pass but got {score}... 😅{RESET}\n")

    os.system('cls' if os.name == 'nt' else 'clear')
    return score, pass_score

# ============================================================
#  [4]  MINIGAME CONFIGS  (loaded from JSON/Minigame.json)
#       and the MinigameState class
#
#       how it works:
#         - a needle bounces left ↔ right on a track
#         - player hits SPACE (or the button) to "stop" it
#         - if needle lands in the green zone  →  HIT ✓
#         - if it lands in the red danger zone →  MISS ✗
#         - win 3/3 rounds to pass the minigame
# ============================================================
with open(resource_path("JSON/Minigame.json"), "r") as f:
    _mg_json = json.load(f)

# colors in JSON are [r,g,b] lists — convert to tuples for pygame
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
    """
    handles ONE minigame session (needle bar mini-game)
    created fresh each time a minigame popup opens
    """

    # track bounds and appearance — pulled from JSON
    TRACK_LEFT     = MINIGAME_BAR["track_left"]
    TRACK_RIGHT    = MINIGAME_BAR["track_right"]
    TRACK_Y        = MINIGAME_BAR["track_y"]
    TRACK_H        = MINIGAME_BAR["track_h"]
    DANGER_W       = MINIGAME_BAR["danger_zone_w"]
    TRACK_W        = TRACK_RIGHT - TRACK_LEFT
    TOTAL_ROUNDS   = 3             # must win all 3 to pass
    FLASH_DURATION = 90            # frames the HIT/MISS text stays on screen

    def __init__(self, minigame_name):
        cfg = MINIGAME_CONFIGS.get(minigame_name, MINIGAME_CONFIGS["minigame1"])
        self.cfg           = cfg
        self.name          = minigame_name

        # needle position & movement
        self.needle_x      = float(self.TRACK_LEFT)
        self.direction     = 1
        self.current_speed = cfg["speed"]

        # round tracking
        self.round  = 0
        self.wins   = 0
        self.done   = False
        self.passed = False

        # green zone — placed randomly each round
        self.green_left  = 0
        self.green_right = 0
        self._place_green()

        # feedback flash (HIT! / MISS!)
        self.flash_timer = 0
        self.flash_text  = ""
        self.flash_color = (255, 255, 255)

        # particle burst on hit/miss
        self.particles = []

        # fonts — created once, reused every frame
        self._font_big   = pygame.font.SysFont("consolas", 26, bold=True)
        self._font_small = pygame.font.SysFont("consolas", 16, bold=True)
        self._font_round = pygame.font.SysFont("consolas", 18, bold=True)

    # ── internal helpers ─────────────────────────────────────

    def _place_green(self):
        """randomize the green zone position for a new round"""
        gw = int(self.TRACK_W * self.cfg["green_w_frac"])
        max_left = self.TRACK_RIGHT - gw - 20
        self.green_left  = random.randint(self.TRACK_LEFT + 20, max_left)
        self.green_right = self.green_left + gw

    def _lerp_color(self, c1, c2, t):
        """linear interpolate between two RGB tuples"""
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

    def _burst(self, x, y, color):
        """spawn a bunch of particles at (x, y) — called on hit/miss"""
        for _ in range(18):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(2, 6)
            self.particles.append({
                "x":     x,
                "y":     y,
                "vx":    math.cos(angle) * speed,
                "vy":    math.sin(angle) * speed - 2,
                "color": color,
                "life":  1.0,
                "size":  random.randint(3, 7),
            })

    # ── public methods ────────────────────────────────────────

    def hit(self):
        """
        called when the player presses the hit button.
        checks if needle is in the green zone, updates score.
        does nothing if the game is already done or mid-flash.
        """
        if self.done or self.flash_timer > 0:
            return

        nx = self.needle_x
        if self.green_left <= nx <= self.green_right:
            self.wins       += 1
            self.flash_text  = f"HIT!  ({self.wins}/{self.TOTAL_ROUNDS})"
            self.flash_color = self.cfg["green_color"]
            self._burst(int(nx), self.TRACK_Y, self.cfg["green_color"])
        else:
            self.flash_text  = "MISS!"
            self.flash_color = (230, 60, 60)
            self._burst(int(nx), self.TRACK_Y, (230, 60, 60))

        self.flash_timer = self.FLASH_DURATION
        self.round      += 1

        # check if all rounds are done
        if self.round >= self.TOTAL_ROUNDS:
            self.done   = True
            self.passed = (self.wins == self.TOTAL_ROUNDS)

    def update(self):
        """
        called every frame.
        moves the needle, counts down flash, moves particles.
        """
        if self.done:
            return

        if self.flash_timer > 0:
            self.flash_timer -= 1
            if self.flash_timer == 0 and not self.done:
                # start the next round — place new green zone, speed up a bit
                self._place_green()
                self.current_speed += self.cfg["speed_increment"]
                self.needle_x       = float(self.TRACK_LEFT)
                self.direction      = 1
        else:
            # bounce the needle back and forth
            self.needle_x += self.current_speed * self.direction
            if self.needle_x >= self.TRACK_RIGHT:
                self.needle_x = float(self.TRACK_RIGHT)
                self.direction = -1
            elif self.needle_x <= self.TRACK_LEFT:
                self.needle_x = float(self.TRACK_LEFT)
                self.direction = 1

        # update particles (gravity + fade)
        for p in self.particles:
            p["x"]    += p["vx"]
            p["y"]    += p["vy"]
            p["vy"]   += 0.25          # gravity
            p["life"] -= 0.04
        self.particles = [p for p in self.particles if p["life"] > 0]

    def draw(self, surface):
        """draws the whole minigame bar + needle + particles + flash text"""
        cfg = self.cfg
        TL  = self.TRACK_LEFT
        TR  = self.TRACK_RIGHT
        TY  = self.TRACK_Y
        TH  = self.TRACK_H
        TW  = self.TRACK_W

        top = TY - TH // 2

        # ── round indicator dots ──────────────────────────────
        for i in range(self.TOTAL_ROUNDS):
            cx     = SCREEN_WIDTH // 2 + (i - self.TOTAL_ROUNDS // 2) * 28 + 14
            filled = i < self.round
            pygame.draw.circle(
                surface,
                cfg["green_color"] if filled else (80, 80, 100),
                (cx, top - 22), 8
            )
            if filled:
                pygame.draw.circle(surface, (255, 255, 255), (cx, top - 22), 4)

        rnd_txt = self._font_round.render(
            f"Round {min(self.round + 1, self.TOTAL_ROUNDS)}/{self.TOTAL_ROUNDS}",
            True, (200, 200, 220))
        surface.blit(rnd_txt, (TL, top - 32))

        # ── track background ──────────────────────────────────
        shadow_rect = pygame.Rect(TL + 3, top + 5, TW, TH)
        pygame.draw.rect(surface, (10, 10, 20), shadow_rect, border_radius=10)

        track_rect = pygame.Rect(TL, top, TW, TH)
        pygame.draw.rect(surface, cfg["track_color"], track_rect, border_radius=10)

        # ── red danger zones on each end ─────────────────────
        dw = 25
        pygame.draw.rect(surface, cfg["danger_color"], pygame.Rect(TL,      top, dw, TH), border_radius=10)
        pygame.draw.rect(surface, cfg["danger_color"], pygame.Rect(TR - dw, top, dw, TH), border_radius=10)

        # ── green hit zone ────────────────────────────────────
        gw = self.green_right - self.green_left
        gz = pygame.Rect(self.green_left, top, gw, TH)
        pygame.draw.rect(surface, cfg["green_color"], gz, border_radius=7)

        # highlight stripe on green zone
        hl     = pygame.Rect(self.green_left + 4, top + 4, gw - 8, 8)
        bright = self._lerp_color(cfg["green_color"], (255, 255, 255), 0.5)
        pygame.draw.rect(surface, bright, hl, border_radius=3)

        # center line on green zone
        gc = (self.green_left + self.green_right) // 2
        pygame.draw.line(surface, (255, 255, 255), (gc, top + 3), (gc, top + TH - 3), 2)

        # track border
        pygame.draw.rect(surface, (80, 80, 110), track_rect, 2, border_radius=10)

        # ── needle ────────────────────────────────────────────
        if self.flash_timer == 0 or not self.done:
            nx = int(self.needle_x)
            pygame.draw.line(surface, (0, 0, 0),             (nx + 2, top - 12), (nx + 2, top + TH + 12), 4)
            pygame.draw.line(surface, cfg["needle_color"],   (nx,     top - 12), (nx,     top + TH + 12), 3)
            pygame.draw.circle(surface, cfg["needle_color"], (nx, top - 12),      5)
            pygame.draw.circle(surface, cfg["needle_color"], (nx, top + TH + 12), 5)
            pygame.draw.circle(surface, (255, 255, 255),     (nx, top - 12),      2)
            pygame.draw.circle(surface, (255, 255, 255),     (nx, top + TH + 12), 2)

        # ── HIT / MISS flash text ─────────────────────────────
        if self.flash_timer > 0:
            t   = self.flash_timer / self.FLASH_DURATION
            sz  = int(20 + 10 * (1 - abs(t - 0.5) * 2))
            fnt = pygame.font.SysFont("consolas", sz, bold=True)
            txt    = fnt.render(self.flash_text, True, self.flash_color)
            shadow = fnt.render(self.flash_text, True, (0, 0, 0))
            cx = SCREEN_WIDTH // 2
            ty = top + TH + 18
            surface.blit(shadow, (cx - txt.get_width() // 2 + 2, ty + 2))
            surface.blit(txt,    (cx - txt.get_width() // 2,     ty))

        # ── ALL HIT / FAILED result ───────────────────────────
        if self.done:
            msg = "ALL HIT! ✓" if self.passed else f"FAILED ({self.wins}/3)"
            col = cfg["green_color"] if self.passed else (230, 60, 60)
            txt = self._font_big.render(msg, True, col)
            shd = self._font_big.render(msg, True, (0, 0, 0))
            cx  = SCREEN_WIDTH // 2
            ty  = top + TH + 20
            surface.blit(shd, (cx - txt.get_width() // 2 + 2, ty + 2))
            surface.blit(txt, (cx - txt.get_width() // 2,     ty))

        # ── particles ─────────────────────────────────────────
        for p in self.particles:
            alpha = max(0, p["life"])
            col   = self._lerp_color(p["color"], (0, 0, 0), 1 - alpha)
            r     = max(1, int(p["size"] * alpha))
            pygame.draw.circle(surface, col, (int(p["x"]), int(p["y"])), r)

        # label at the top
        lbl = self._font_small.render(f"[ {cfg['label']} MINIGAME ]", True, (160, 160, 200))
        surface.blit(lbl, (TL, top - 52))


# ============================================================
#  [5]  POPUP CLASS
#       popups slide in from the top of the screen,
#       do a little bounce (bob), then sit still.
#       clicking on them (if closable) slides them back out.
# ============================================================
class Popup:
    OFFSCREEN_Y   = -400    # starting position (above screen)
    SLIDE_SPEED   = 35      # px/frame while entering
    BOB_STRENGTH  = -8      # initial upward velocity after landing
    GRAVITY       = 1.2     # how fast it falls back down
    BOB_DAMPEN    = 0.55    # fraction of velocity kept each bounce (e.g. 0.55 = 55% kept)
    BOB_STOP      = 1.5     # stop bobbing below this velocity
    SLIDE_OUT_SPD = 22      # px/frame while exiting

    def __init__(self, image_path, size, target_y, unclickable=True):
        self.image       = load_scaled_image(image_path, size)
        self.rect        = self.image.get_rect(centerx=SCREEN_WIDTH // 2, top=self.OFFSCREEN_Y)
        self.target_y    = target_y
        self.unclickable = unclickable  # if True, clicking the popup closes it
        self.state       = None         # 'slide_in' | 'bob' | 'slide_out' | None
        self.vel         = 0.0
        self.active      = False
        self.minigame    = None         # MinigameState attached to this popup (if any)

    def open(self, sound=None):
        """make the popup appear and slide in from the top"""
        self.rect.top = self.OFFSCREEN_Y
        self.vel      = self.SLIDE_SPEED
        self.state    = 'slide_in'
        self.active   = True
        if sound:
            sound.play()

    def close(self):
        """start the slide-out animation"""
        if self.active and self.state != 'slide_out':
            self.vel   = self.SLIDE_OUT_SPD
            self.state = 'slide_out'

    def handle_event(self, event):
        """returns True if click closed the popup"""
        if not self.active:
            return False
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.rect.collidepoint(event.pos) and self.unclickable:
                self.close()
                return True
        return False

    def update(self):
        """move the popup each frame based on current state"""
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
                    self.state = None   # settled — minigame can now start

        elif self.state == 'slide_out':
            self.rect.top += self.vel
            if self.rect.top > SCREEN_HEIGHT:
                self.active   = False
                self.state    = None
                self.minigame = None

        # tick minigame only when the popup is fully settled
        if self.minigame and self.state is None:
            self.minigame.update()

    def draw(self, surface):
        if not self.active:
            return
        # darken the background behind the popup
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        surface.blit(self.image, self.rect)
        # draw embedded minigame on top (only when settled)
        if self.minigame and self.state is None:
            self.minigame.draw(surface)


# ============================================================
#  [6]  BUTTON CLASS
#       two images: normal and pressed.
#       returns True from handle_event only on a full click
#       (mouse down AND up on the same button).
# ============================================================
class Button:
    def __init__(self, image1_path, image2_path, position, size):
        self.image_normal  = load_scaled_image(image1_path, size)
        self.image_pressed = load_scaled_image(image2_path, size)
        self.current_image = self.image_normal
        self.rect          = self.current_image.get_rect(center=position)
        self.is_holding    = False

    def handle_event(self, event):
        """returns True on a completed click (down + up on this button)"""
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


# ============================================================
#  [7]  FADE TRANSITION
#       fades the screen to a solid blue color, runs a callback
#       at peak darkness, then fades back in.
#       used for scene switches (menu → game, etc.)
# ============================================================
class Fade:
    FADE_IN_SPEED  = 5   # alpha added per frame (0→255)
    FADE_OUT_SPEED = 5   # alpha removed per frame (255→0)

    def __init__(self):
        self.overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.overlay.fill((15, 58, 78))   # dark teal-blue
        self.alpha       = 0
        self.state       = None           # 'fade_in' | 'fade_out' | None
        self.on_complete = None           # callback fired at peak opacity

    @property
    def active(self):
        return self.state is not None

    def start(self, on_peak_callback=None):
        """kick off a fade — callback fires when fully black (before fade out)"""
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


# ============================================================
#  [8]  GAME STATE
#       holds everything that needs to survive between frames:
#       current scene, selected character, week number, stats.
#
#       stats layout:
#         [0] stress       ← inverted: high = bad!
#         [1] happiness
#         [2] grades
#         [3] intelligence
# ============================================================
class GameState:
    def __init__(self):
        self.running            = True
        self.playing_video      = True
        self.week               = 0
        self.scene              = "menu"
        self.gender             = None
        self.selected_char      = None
        self.pending_quiz       = False                 # set to True to trigger NCE quiz next frame
        self.pending_quiz_role  = "NCE"
        self.quiz_just_finished = False
        self.stats              = [0, 0, 0, 0]          # actual values
        self.stats_display      = [0.0, 0.0, 0.0, 0.0]  # smoothed for the bar animation
        self.pending_mg_result  = None
        self.month_schedules    = {}
        self.week_label_timer   = 0
        self.week_label_text    = ""
        self.used_friend_bully = set()
        self.used_minigames = set()

    def apply_char_stats(self, char):
        """copy starting stats from the selected character's JSON entry"""
        self.stats = [
            char.get("starting_stress",       20),
            char.get("starting_happiness",    40),
            char.get("starting_grades",       30),
            char.get("starting_intelligence",  0),
        ]
        self.stats_display = [float(v) for v in self.stats]

    def get_month_schedule(self, month):
        """returns the 4-event order for this month, generating it if needed"""
        if month not in self.month_schedules:
            order = ['lore', 'minigame', 'quiz', 'free_day']
            if month in (1, 8):
                pass  # fixed order — don't shuffle
            else:
                random.shuffle(order)
            self.month_schedules[month] = order
        return self.month_schedules[month]


# ============================================================
#  [9]  ASSET LOADING
#       loads EVERYTHING at startup so nothing lags mid-game.
#       returns one big `assets` dict used throughout the code.
# ============================================================
CHAR_IMG_SIZE = (700, 382)   # all character portraits are this size

def load_chars_from_json(json_file, char_images):
    """load character data from JSON and pre-load their portrait images"""
    with open(resource_path(json_file), "r") as f:
        chars = json.load(f)
    for char in chars:
        key = char['Appearance']
        if key not in char_images:
            char_images[key] = load_scaled_image(key, CHAR_IMG_SIZE)
    return chars


def load_assets():
    assets = {}

    # video (plays on startup)
    assets['intro_video'] = MediaPlayer(resource_path("Assets/GameIntro.mov"))

    # sound effects
    assets['button_click'] = pygame.mixer.Sound(resource_path("Assets/ButtonClicked.mp3"))
    assets['slide_in']     = pygame.mixer.Sound(resource_path("Assets/slide_in.mp3"))
    assets['skip_clicked'] = pygame.mixer.Sound(resource_path("Assets/skip_clicked.mp3"))
    assets['game_over']    = pygame.mixer.Sound(resource_path("Assets/GameOver.mp3"))
    assets['happy']        = pygame.mixer.Sound(resource_path("Assets/Happy.wav"))
    assets['sad']          = pygame.mixer.Sound(resource_path("Assets/Sad.wav"))

    # background images
    assets['main_game_image'] = load_scaled_image("Assets/MainGame.png", (SCREEN_WIDTH, SCREEN_HEIGHT))
    assets['main_menu_image'] = load_scaled_image("Assets/Menu.png",     (SCREEN_WIDTH, SCREEN_HEIGHT))

    # character portraits (sorted by gender for the selection screen)
    assets['char_images'] = {}
    all_chars             = load_chars_from_json("JSON/Characters.json", assets['char_images'])
    assets['boys_chars']  = [c for c in all_chars if c['Gender'] == 'Male']
    assets['girls_chars'] = [c for c in all_chars if c['Gender'] == 'Female']

    return assets


# ============================================================
#  [10] BUTTON & POPUP FACTORY
#       creates all the buttons and popups used in the game.
#       most come from JSON/Popup.json — see load_popups_from_json()
#       below for how that works.
# ============================================================
def create_buttons_and_popups():
    popups, buttons = load_popups_from_json("JSON/Popup.json")

    # hard-coded menu buttons (not in the popup JSON)
    buttons['menu_start']   = Button("Buttons/StartGameButton.png", "Buttons/StartGameAnimation.png", (338, 385), (474, 109))
    buttons['menu_details'] = Button("Buttons/DetailsButton.png",   "Buttons/DetailsAnimation.png",   (338, 565), (474, 109))
    buttons['skip']         = Button("Buttons/Skip.png",            "Buttons/SkipAnimation.png",      (120, 655), (128, 130))

    return buttons, popups


# ============================================================
#  [11] VIDEO PLAYBACK
#       ffpyplayer feeds us frames as raw RGB buffers.
#       we blit each frame to the screen until 'eof' is returned.
# ============================================================
def handle_video(assets, game_state):
    frame, val = assets['intro_video'].get_frame()

    if val == 'eof':
        # video finished → switch to menu
        game_state.playing_video = False
        screen.blit(assets['main_menu_image'], (0, 0))
        pygame.display.update()
        assets['intro_video'].close_player()
        return

    if frame is not None:
        img, _ = frame
        surface = pygame.transform.scale(
            pygame.image.frombuffer(img.to_bytearray()[0], img.get_size(), 'RGB'),
            (SCREEN_WIDTH, SCREEN_HEIGHT)
        )
        screen.blit(surface, (0, 0))


# ============================================================
#  [12] JSON-BASED POPUP + BUTTON LOADER
#       reads JSON/Popup.json and builds Popup + Button objects.
#
#       JSON structure per entry:
#         name, image, size, target_y, closable, buttons[ ]
#       each button has: image, image_anim, size, offset_y, role, stats
# ============================================================
def load_popups_from_json(json_file="JSON/Popup.json"):
    with open(resource_path(json_file), "r") as f:
        data = json.load(f)

    popups  = {}
    buttons = {}

    for entry in data:
        name = entry["name"]
        w, h = entry["size"]

        popup             = Popup(entry["image"], (w, h), target_y=entry["target_y"], unclickable=entry["closable"])
        popup.button_data = entry.get("buttons", [])
        popup.json_stats  = entry.get("stats", {})   # ← stats applied when this popup is clicked closed
        popups[name]      = popup

        for i, btn_data in enumerate(popup.button_data):
            key            = f"{name}_{i}"
            buttons[key]   = Button(btn_data["image"], btn_data["image_anim"], (0, 0), tuple(btn_data["size"]))
            buttons[key].role  = btn_data["role"]
            buttons[key].stats = btn_data.get("stats", {})

    return popups, buttons


# ============================================================
#  MINIGAME NAME LIST  (minigame1 through minigame8)
# ============================================================

ALL_MINIGAMES = [f"minigame{i}" for i in range(1, 9)]

def is_minigame_popup(name):
    return name in ALL_MINIGAMES


# ============================================================
#  [13] EVENT HANDLING — MENU SCENE
#       handles clicks on the main menu screen:
#         Start Game → opens gender popup → fade to game
#         Details    → opens the details popup (info screen)
# ============================================================
def handle_menu_events(buttons, popups, game_state, event, blue_fade, assets):
    if blue_fade.active:
        return   # ignore input while fading

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
                    game_state.gender        = "boy"
                    game_state.selected_char = random.choice(assets['boys_chars'])
                elif btn.role == "gender_girl":
                    game_state.gender        = "girl"
                    game_state.selected_char = random.choice(assets['girls_chars'])

                game_state.apply_char_stats(game_state.selected_char)

                def switch_to_game():
                    popups['gender'].active = False
                    popups['gender'].state  = None
                    game_state.scene        = 'game'
                    popups['nce'].open(sound=assets['slide_in'])

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


# ============================================================
#  [14] EVENT HANDLING — GAME SCENE
#
#       week cycle (repeats every 4 weeks):
#         week % 4 == 1  → friend or bully encounter
#         week % 4 == 2  → minigame
#         week % 4 == 3  → free (nothing happens)
#         week % 4 == 0  → free day popup
#
#       stat indexes (used by apply_stats):
#         0 = stress  |  1 = happiness  |  2 = grades  |  3 = intelligence
# ============================================================
QUIZ_POPUP_MAP = {
    "Math Quiz":         "Math Quiz",
    "Math Long Test":    "Exam",
    "Science Quiz":      "Science Quiz",
    "Science Long Test": "Exam",
    "English Quiz":      "English Quiz",
    "English Long Test": "Exam",
    "Mix Quiz":          "Mix Quiz",
    "Mix Long Test":     "Exam",
}

STAT_INDEX = {
    "stress":       0,
    "happiness":    1,
    "grades":       2,
    "intelligence": 3,
}

def apply_stats(game_state, stats):
    """add (or subtract) stat changes, clamped to [0, 100]"""
    for stat, value in stats.items():
        idx = STAT_INDEX.get(stat)
        if idx is not None:
            game_state.stats[idx] = max(0, min(100, game_state.stats[idx] + value))

def check_stat_game_overs(game_state, popups, assets):
    if game_state.stats[1] == 0:
        popups['gameover3'].open(sound=assets['game_over'])
    elif game_state.stats[2] == 0:
        popups['gameover4'].open(sound=assets['game_over'])

def apply_passive_penalties(game_state):
    """
    called every time the skip button is pressed.
    stress >= 80       → happiness -5
    intelligence <= 20 → grades   -5
    game-over checks are handled by the caller after this returns,
    so we only touch stats here — no popup logic.
    """
    stress       = game_state.stats[0]
    happiness    = game_state.stats[1]
    grades       = game_state.stats[2]
    intelligence = game_state.stats[3]

    # ── stress penalty ────────────────────────────────────────
    if stress >= 80:
        game_state.stats[1] = max(0, happiness - 5)

    # ── intelligence penalty ──────────────────────────────────
    if intelligence <= 20:
        game_state.stats[2] = max(0, grades - 5)


def handle_game_events(buttons, popups, game_state, event, blue_fade, assets):
    if blue_fade.active:
        return

    any_popup_active = any(p.active for p in popups.values())

    # ── SKIP button (advances the week) ──────────────────────
    if not any_popup_active:
        if buttons['skip'].handle_event(event):
            assets['skip_clicked'].play()

            if game_state.quiz_just_finished:
                os.system('cls' if os.name == 'nt' else 'clear')
                game_state.quiz_just_finished = False

            game_state.week += 1
            apply_passive_penalties(game_state)   # stat math only
            check_stat_game_overs(game_state, popups, assets)  # one single check after

            if 1 <= game_state.week <= 32:
                month         = (game_state.week - 1) // 4 + 1
                week_in_month = (game_state.week - 1) % 4 + 1
                game_state.week_label_text  = f"Month {month}  -  Week {week_in_month}"
                game_state.week_label_timer = 180

            if game_state.week == 32:
                game_state.week = 0
                popups['WINNER'].open(sound=assets['happy'])

            elif game_state.week == 0:
                popups['nce'].open(sound=assets['slide_in'])
            else:
                month         = (game_state.week - 1) // 4 + 1
                week_in_month = (game_state.week - 1) % 4  # 0, 1, 2, 3
                schedule      = game_state.get_month_schedule(month)
                event_type    = schedule[week_in_month]

                if event_type == 'lore':
                    ALL_FRIEND_BULLY = [
                        'friend1', 'friend2', 'friend3', 'friend4', 'friend5', 'friend6',
                        'bully1', 'bully2', 'bully3', 'bully4',
                    ]
                    pool = [p for p in ALL_FRIEND_BULLY if p not in game_state.used_friend_bully]
                    if not pool:
                        game_state.used_friend_bully.clear()
                        pool = ALL_FRIEND_BULLY
                    chosen = random.choice(pool)
                    game_state.used_friend_bully.add(chosen)
                    popups[chosen].open(sound=assets['slide_in'])

                elif event_type == 'minigame':
                    mg_pool = [m for m in ALL_MINIGAMES if m not in game_state.used_minigames]
                    if not mg_pool:
                        game_state.used_minigames.clear()
                        mg_pool = ALL_MINIGAMES
                    chosen_mg = random.choice(mg_pool)
                    game_state.used_minigames.add(chosen_mg)
                    popups[chosen_mg].open(sound=assets['slide_in'])

                elif event_type == 'quiz':
                    if month in MONTH_QUIZ_SCHEDULE:
                        role      = MONTH_QUIZ_SCHEDULE[month]
                        popup_key = QUIZ_POPUP_MAP.get(role)
                        game_state.pending_quiz_role = role
                        if popup_key and popup_key in popups:
                            popups[popup_key].open(sound=assets['slide_in'])
                        else:
                            game_state.pending_quiz = True

                elif event_type == 'free_day':
                    popups['free day'].open(sound=assets['slide_in'])

    # ── NCE QUIZ popup ────────────────────────────────────────
    if popups['nce'].active:
        popups['nce'].handle_event(event)
        for key, btn in buttons.items():
            if not key.startswith("nce_"):
                continue
            if btn.handle_event(event):
                assets['button_click'].play()
                if btn.role == "nce_quiz":
                    apply_stats(game_state, btn.stats)
                    popups['nce'].close()
                    game_state.pending_quiz      = True
                    game_state.pending_quiz_role = "NCE"
                elif btn.role == "nce_close":
                    # skipped the quiz → immediate game over
                    popups['nce'].active = False
                    popups['nce'].state  = None
                    popups['gameover1'].open(sound=assets['game_over'])

    # ── FREE DAY popup ────────────────────────────────────────
    if popups['free day'].active:
        popup = popups['free day']
        for key, btn in buttons.items():
            if not key.startswith('free day_'):
                continue
            if btn.handle_event(event):
                assets['button_click'].play()
                apply_stats(game_state, btn.stats)   # ← applies stats straight from JSON
                popup.active = False
                popup.state  = None
                role = btn.role

                if role == 'do nothing':
                    popups['relaxing'].open(sound=assets['happy'])
                elif role == 'find friend':
                    popups['hangout'].open(sound=assets['happy'])
                elif role == 'extra credit':
                    popups['tryhard'].open(sound=assets['happy'])
                elif role == 'read books':
                    popups[random.choice(['Scissor', 'WAP', 'Corpus'])].open(sound=assets['happy'])

    # ── MINIGAME popups ───────────────────────────────────────
    for mg_name in ALL_MINIGAMES:
        popup = popups[mg_name]
        if not popup.active:
            continue

        # create the minigame state once the popup settles
        if popup.state is None and popup.minigame is None:
            popup.minigame = MinigameState(mg_name)

        mg  = popup.minigame
        key = f"{mg_name}_0"

        if key in buttons:
            btn = buttons[key]
            if popup.button_data:
                btn.rect.center = (SCREEN_WIDTH // 2, popup.rect.top + popup.button_data[0]["offset_y"])

            if mg and not mg.done:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and btn.rect.collidepoint(event.pos):
                    assets['button_click'].play()
                    mg.hit()
            elif mg and mg.done:
                # show result popup (pass or fail)
                if btn.handle_event(event):
                    assets['button_click'].play()
                    passed         = mg.passed
                    popup.active   = False
                    popup.state    = None
                    popup.minigame = None
                    rkey  = f"mg{mg_name[-1]}p{'1' if passed else '2'}"
                    sound = assets['happy'] if passed else assets['sad']
                    if rkey in popups:
                        popups[rkey].open(sound=sound)

    # ── RESULT popups (close on click → apply their json_stats) ──
    # note: friend1popup2 and friend2popup2 are intentionally absent —
    # they have no routing code and are never opened anywhere.
    # b4p3 is also removed for the same reason.
    RESULT_POPUPS_WITH_STATS = [
        'friend1popup1', 'friend1popup3',
        'friend2popup1', 'friend2popup3',
        'f3p1', 'f3p2', 'f4p1', 'f4p2', 'f5p1', 'f5p2', 'f6p1', 'f6p2',
        'b1p1', 'b1p2', 'b2p1', 'b2p2', 'b3p1', 'b3p2', 'b4p1', 'b4p2',
        'mg1p1', 'mg1p2', 'mg2p1', 'mg2p2', 'mg3p1', 'mg3p2',
        'mg4p1', 'mg4p2', 'mg5p1', 'mg5p2', 'mg6p1', 'mg6p2',
        'mg7p1', 'mg7p2', 'mg8p1', 'mg8p2',
        'relaxing', 'hangout', 'tryhard', 'Scissor', 'WAP', 'Corpus', 'Sick',
    ]

    for key in RESULT_POPUPS_WITH_STATS:
        if key not in popups or not popups[key].active:
            continue
        if popups[key].handle_event(event):   # returns True on click-close
            apply_stats(game_state, popups[key].json_stats)
            check_stat_game_overs(game_state, popups, assets)

    # ── FRIEND / BULLY choice popups ─────────────────────────
    FRIEND_BULLY_POPUPS = {
        'friend1': {'friends!': 'friend1popup1', 'not friends': 'friend1popup3'},
        'friend2': {'friends!': 'friend2popup1', 'not friends': 'friend2popup3'},
        'friend3': {'friends!': 'f3p1',          'not friends': 'f3p2'},
        'friend4': {'friends!': 'f4p1',          'not friends': 'f4p2'},
        'friend5': {'friends!': 'f5p1',          'not friends': 'f5p2'},
        'friend6': {'friends!': 'f6p1',          'not friends': 'f6p2'},
        'bully1':  {'not bullied': 'b1p1',       'bullied!': 'b1p2'},
        'bully2':  {'bullied!': 'b2p1',          'not bullied': 'b2p2'},
        'bully3':  {'bullied!': 'b3p1',          'not bullied': 'b3p2'},
        'bully4':  {'bullied!': 'b4p1',          'not bullied': 'b4p2'},
    }

    # ── QUIZ / EXAM announcement popups ──────────────────────
    for popup_key in ("Math Quiz", "Science Quiz", "English Quiz", "Mix Quiz", "Exam"):
        popup = popups.get(popup_key)
        if not popup or not popup.active:
            continue
        for key, btn in buttons.items():
            if not key.startswith(popup_key + "_"):
                continue
            if btn.handle_event(event):
                assets['button_click'].play()
                popup.active = False
                popup.state  = None
                if btn.role == "take it":
                    game_state.pending_quiz = True
                elif btn.role == "act sick":
                    apply_stats(game_state, {'stress': 15, 'grades': -10, 'happiness': -5})
                    popups['Sick'].open(sound=assets['sad'])

    for popup_name, role_map in FRIEND_BULLY_POPUPS.items():
        popup = popups[popup_name]
        if not popup.active:
            continue
        for key, btn in buttons.items():
            if not key.startswith(popup_name + "_"):
                continue
            if btn.handle_event(event):
                assets['button_click'].play()
                apply_stats(game_state, btn.stats)
                check_stat_game_overs(game_state, popups, assets)
                result = role_map.get(btn.role)
                if result and result in popups:
                    sound        = assets['happy'] if btn.role in ('friends!', 'not bullied') else assets['sad']
                    popup.active = False
                    popup.state  = None
                    popups[result].open(sound=sound)

    # ── GAME OVER buttons ─────────────────────────────────────
    for popup_name in ('gameover1', 'gameover2', 'gameover3', 'gameover4'):
        popup = popups[popup_name]
        if not popup.active:
            continue
        for key, btn in buttons.items():
            if not key.startswith(popup_name + "_"):
                continue
            if btn.handle_event(event):
                assets['button_click'].play()
                popup.active = False
                popup.state  = None
                blue_fade.start(on_peak_callback=lambda: setattr(game_state, 'scene', 'menu'))

    # ── WINNER popup ──────────────────────────────────────────
    if popups['WINNER'].active:
        for key, btn in buttons.items():
            if not key.startswith("WINNER_"):
                continue
            if btn.handle_event(event):
                assets['button_click'].play()
                popups['WINNER'].active = False
                popups['WINNER'].state = None
                blue_fade.start(on_peak_callback=lambda: setattr(game_state, 'scene', 'menu'))

# ============================================================
#  [15] UPDATE — POPUPS
#       advances every popup's animation state each frame.
#       kept here instead of inside the draw functions so that
#       update and render logic stay cleanly separated.
# ============================================================
def update_popups(popups):
    for popup in popups.values():
        popup.update()


# ============================================================
#  [16] DRAWING — MENU SCENE
# ============================================================
def draw_menu(screen, buttons, popups):
    buttons['menu_start'].draw(screen)
    buttons['menu_details'].draw(screen)

    for popup in popups.values():
        popup.draw(screen)

    # position gender buttons relative to the popup's current position
    if popups['gender'].active:
        popup_top = popups['gender'].rect.top
        for key, btn in buttons.items():
            if not key.startswith("gender_"):
                continue
            idx = int(key.split("_")[1])
            btn.rect.center = (337, popup_top + popups['gender'].button_data[idx]["offset_y"])
            btn.draw(screen)


# ============================================================
#  [17] DRAWING — GAME SCENE
#
#       stat bars:
#         bar 0 (stress)  → inverted color logic (high = red)
#         bars 1-3        → normal (high = green)
# ============================================================
def draw_stat_bar(surface, stat_display, bar_x, bar_y, bar_w=250, bar_h=16, label="", invert=False):
    """draw a single stat bar with a label, percentage, and colour based on value"""
    COLOR_HIGH = (144, 238, 144)   # green
    COLOR_MID  = (255, 215,   0)   # yellow
    COLOR_LOW  = (255, 153, 153)   # red/pink

    pct = max(0.0, min(100.0, stat_display))
    if invert:
        color = COLOR_LOW if pct >= 80 else COLOR_MID if pct >= 21 else COLOR_HIGH
    else:
        color = COLOR_HIGH if pct >= 80 else COLOR_MID if pct >= 21 else COLOR_LOW

    # label (drawn to the left of the bar)
    if label:
        font_lbl = pygame.font.SysFont("Segoe UI", 12, bold=True)
        lbl      = font_lbl.render(label, True, (255, 255, 255))
        surface.blit(lbl, (bar_x - lbl.get_width() - 8, bar_y + bar_h // 2 - lbl.get_height() // 2))

    # background track
    pygame.draw.rect(surface, (60, 60, 70), (bar_x, bar_y, bar_w, bar_h), border_radius=6)

    # filled portion
    fill_w = int(bar_w * pct / 100)
    if fill_w > 0:
        pygame.draw.rect(surface, color, (bar_x, bar_y, fill_w, bar_h), border_radius=6)

    # white border
    pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=6)

    # percentage text centered on the bar
    font = pygame.font.SysFont("Segoe UI", 12, bold=True)
    txt  = font.render(f"{int(round(pct))}%", True, (255, 255, 255))
    surface.blit(txt, txt.get_rect(center=(bar_x + bar_w // 2, bar_y + bar_h // 2)))


def draw_game(screen, assets, game_state, buttons, popups):
    screen.blit(assets['main_game_image'], (0, 0))

    # draw the selected character portrait
    if game_state.selected_char:
        face_img = assets['char_images'][game_state.selected_char['Appearance']]
        screen.blit(face_img, (-7, -1))

    # stat bars — positions tuned to fit the MainGame.png layout
    BAR_X       = 290
    BAR_START_Y = 377
    BAR_GAP     = 51
    BAR_W       = 310
    BAR_H       = 25

    for i in range(4):
        # smoothly animate bars toward their target value (lerp 12%)
        diff = game_state.stats[i] - game_state.stats_display[i]
        game_state.stats_display[i] += diff * 0.12
        draw_stat_bar(
            screen,
            game_state.stats_display[i],
            bar_x=BAR_X,
            bar_y=BAR_START_Y + i * BAR_GAP,
            bar_w=BAR_W,
            bar_h=BAR_H,
            invert=(i == 0)   # stress bar: high is bad
        )

    buttons['skip'].draw(screen)

    # ── regular popups ────────────────────────────────────────
    regular_popups = [
        'nce',
        'friend1', 'friend2', 'friend3', 'friend4', 'friend5', 'friend6',
        'bully1',  'bully2',  'bully3',  'bully4',
        'gameover1', 'gameover2', 'gameover3', 'gameover4',
        'friend1popup1', 'friend1popup3',
        'friend2popup1', 'friend2popup3',
        'f3p1', 'f3p2', 'f4p1', 'f4p2', 'f5p1', 'f5p2', 'f6p1', 'f6p2',
        'b1p1', 'b1p2', 'b2p1', 'b2p2', 'b3p1', 'b3p2', 'b4p1', 'b4p2',
        'mg1p1', 'mg1p2', 'mg2p1', 'mg2p2', 'mg3p1', 'mg3p2',
        'mg4p1', 'mg4p2', 'mg5p1', 'mg5p2', 'mg6p1', 'mg6p2',
        'mg7p1', 'mg7p2', 'mg8p1', 'mg8p2',
        'Math Quiz', 'Science Quiz', 'English Quiz', 'Mix Quiz', 'Exam',
        'free day',
        'relaxing', 'hangout', 'tryhard', 'Scissor', 'WAP', 'Corpus', 'Sick',
        'WINNER'
    ]

    for pname in regular_popups:
        if pname not in popups:
            continue
        popup = popups[pname]
        popup.draw(screen)

        # draw that popup's buttons at the correct offset position
        prefix = pname + "_"
        if popup.active:
            popup_top = popup.rect.top
            for key, btn in buttons.items():
                if not key.startswith(prefix):
                    continue
                idx = int(key.split("_")[-1])
                if idx < len(popup.button_data):
                    btn.rect.center = (349, popup_top + popup.button_data[idx]["offset_y"])
                btn.draw(screen)

    # ── minigame popups ───────────────────────────────────────
    for mg_name in ALL_MINIGAMES:
        if mg_name not in popups:
            continue
        popup = popups[mg_name]
        popup.draw(screen)

        if popup.active and popup.state is None:
            key = f"{mg_name}_0"
            if key in buttons and popup.button_data:
                buttons[key].rect.center = (343, popup.rect.top + popup.button_data[0]["offset_y"])
                buttons[key].draw(screen)

    # ── Week / Month label (rotated 90°, chalk style) ────────
    if game_state.week_label_timer > 0:
        game_state.week_label_timer -= 1

        # fade out in the last 60 frames
        alpha = min(255, game_state.week_label_timer * 4)

        try:
            chalk_font = pygame.font.SysFont("segoeprint", 36, bold=True)
        except FileNotFoundError:
            chalk_font = pygame.font.SysFont("segoescript", 36)

        label_surf = chalk_font.render(game_state.week_label_text, True, (245, 240, 220))
        label_surf.set_alpha(alpha)

        # rotate 90° counter-clockwise
        rotated = pygame.transform.rotate(label_surf, 90)

        # stick it on the right edge of the screen
        rx = SCREEN_WIDTH - rotated.get_width() - 8
        ry = SCREEN_HEIGHT // 2 - rotated.get_height() // 2
        screen.blit(rotated, (rx, ry))


# ============================================================
#  [18] MAIN LOOP
#       standard pygame loop:
#         poll events → update state → draw → flip
#
#       special case: pending_quiz is checked OUTSIDE the event
#       loop so the terminal quiz can block without freezing pygame.
# ============================================================
def main():
    assets          = load_assets()
    buttons, popups = create_buttons_and_popups()
    game_state      = GameState()
    blue_fade       = Fade()

    while game_state.running:

        # ── event polling ─────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_state.running = False

            if not game_state.playing_video and game_state.scene == "menu":
                handle_menu_events(buttons, popups, game_state, event, blue_fade, assets)

            elif not game_state.playing_video and game_state.scene == "game":
                handle_game_events(buttons, popups, game_state, event, blue_fade, assets)

        # ── NCE quiz (runs blocking in terminal) ──────────────
        if game_state.pending_quiz:
            game_state.pending_quiz = False
            role      = game_state.pending_quiz_role
            json_file = QUIZ_JSON_MAP.get(role, "JSON/NCE.json")
            score, pass_score = run_nce_quiz(json_file=json_file, role=role)
            game_state.quiz_just_finished = True
            passed = score >= pass_score

            if role == "NCE":
                if not passed:
                    popups['gameover2'].open(sound=assets['game_over'])

            elif role in ("Math Long Test", "Science Long Test", "English Long Test", "Mix Long Test"):
                # EXAM — bigger stat swings
                if passed:
                    apply_stats(game_state, {'grades': 15, 'stress': -5, 'happiness': 5})
                else:
                    apply_stats(game_state, {'grades': -15, 'stress': 5, 'happiness': -5})
                check_stat_game_overs(game_state, popups, assets)
            else:
                # QUIZ (Math Quiz, Science Quiz, English Quiz, Mix Quiz)
                if passed:
                    apply_stats(game_state, {'grades': 5, 'happiness': 5})
                else:
                    apply_stats(game_state, {'grades': -5, 'happiness': -5})
                check_stat_game_overs(game_state, popups, assets)

        # ── drawing ───────────────────────────────────────────
        if game_state.playing_video:
            handle_video(assets, game_state)

        elif game_state.scene == "menu":
            screen.blit(assets['main_menu_image'], (0, 0))
            update_popups(popups)
            draw_menu(screen, buttons, popups)
            blue_fade.update()
            blue_fade.draw(screen)

        elif game_state.scene == "game":
            update_popups(popups)
            draw_game(screen, assets, game_state, buttons, popups)
            blue_fade.update()
            blue_fade.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


# ============================================================
#  [19] ENTRY POINT
# ============================================================
if __name__ == "__main__":
    main()

# ============================================================
#  [20] REFERENCES
# ============================================================
"""
GameDev Academy. (2023, November 8). Pygame animation tutorial: Complete guide. GameDev Academy. 
https://gamedevacademy.org/pygame-animation-tutorial-complete-guide/

GeeksforGeeks. (2025, April 28). How to create a pop up in pygame with pgu? GeeksforGeeks. 
https://www.geeksforgeeks.org/python/how-to-create-a-pop-up-in-pygame-with-pgu/

kadir014. (n.d.). pygame-video: Video player for pygame [Source code]. GitHub. 
https://github.com/kadir014/pygame-video

MakeUseOf. (2023, July 12). Adding special effects to pygame games: Particle systems and visual enhancements. MakeUseOf. 
https://www.makeuseof.com/pygame-games-special-effects-particle-systems-visual-enhancements/

PygameVN. (n.d.). Game state management. https://staff6773.github.io/PygameVN/game_state_management/

RipTutorial. (n.d.). Drawing and a basic animation. https://riptutorial.com/pygame/example/17502/drawing-and-a-basic-animation

Tech With Tim. (n.d.). Pygame animation. Tech With Tim. https://www.techwithtim.net/tutorials/game-development-with-python/pygame-tutorial/pygame-animation

Tech With Tim. (2020, January 27). Menus - pygame tutorial [Video]. YouTube. https://www.youtube.com/watch?v=0RryiSjpJn0

Coding Together. (2025, n.d.). Simple snake game in Python #python #coding #programming using pure pygame! [Video]. YouTube. https://www.youtube.com/watch?v=u4Iq4niauCo

DaFluffyPotato. (2023, November 11). How to create particle effects in Python - pygame tutorial [Video]. YouTube. https://www.youtube.com/watch?v=ZiPWN39mGM0

Giraffe Academy. (2017, October 22). Building a multiple choice quiz | Python | Tutorial 32 [Video]. YouTube. https://www.youtube.com/watch?v=SgQhwtIoQ7o

Lmaogg. (2018, March 13). How to fade your screen in pygame [code in description] [Video]. YouTube. https://www.youtube.com/watch?v=H2r2N7D56Uw

Sloth Developer. (2021, October 4). PyGame endless vertical platformer beginner tutorial in Python - Part 9: Fade effect & transitions [Video]. YouTube. https://www.youtube.com/watch?v=m3yWB01hV6Q

Tech with Tim. (2018, March 2). Pygame tutorial #8 - scoring and health bars [Video]. YouTube. https://www.youtube.com/watch?v=JLUqOmE9veI

Tech with Tim. (2020, January 27). Menus - pygame tutorial [Video]. YouTube. https://www.youtube.com/watch?v=0RryiSjpJn0

Tech with Tim. (n.d.). Pygame animation tutorial: How to animate a player character [Video]. YouTube. https://www.youtube.com/watch?v=qPnKIbrVnJk

thenewboston. (2014, December 15). Pygame (Python game development) tutorial - 77 - health bars [Video]. YouTube. https://www.youtube.com/watch?v=TcnWjyHVaOs

Unknown creator. (2021, March 15). Saving and loading in pygame with JSON [Video]. YouTube. https://www.youtube.com/watch?v=__mZO-53PPM

Unknown creator. (2020, June 22). Pygame tutorial - health bars [Video]. YouTube. https://www.youtube.com/watch?v=zY8hIp4KWSM

Unknown creator. (2020, January 5). Making an executable from a pygame game (PyInstaller) [Video]. YouTube. https://www.youtube.com/watch?v=lTxaran0Cig

Unknown creator. (2020, October 2). Creating a health bar in pygame [Dark Souls style] [Video]. YouTube. https://www.youtube.com/watch?v=pUEZbUAMZYA

Unknown creator. (2021, July 31). Pygame saving and loading tutorial: Creating customizable controls [Video]. YouTube. https://www.youtube.com/watch?v=1UCaiX8ESsQ

Unknown creator. (2022, September 7). How to add score and health bar? - Python #PyGame lesson 7 [Video]. YouTube. https://www.youtube.com/watch?v=PgRemhpfUbo

Unknown creator. (2022, December 14). How to create a health bar or inventory status bar in a Python text-based game [Video]. YouTube. https://www.youtube.com/watch?v=oSrjaftUG_8

Unknown creator. (2023, May 6). How to create health bars - pygame tutorial [Video]. YouTube. https://www.youtube.com/watch?v=E82_hdoe06M

Unknown creator. (2024, January 30). Python/Pygame music rhythm game tutorial. ASMR [Video]. YouTube. https://www.youtube.com/watch?v=tYkzrgS5wfE

Unknown creator. (2024, November 23). How to make an executable of your pygame game for Windows using PyInstaller [Video]. YouTube. https://www.youtube.com/watch?v=McFfp3KSimA

Unknown creator. (2025, May 19). Enhancing your pygame rhythm game: Implementing exact timing for smooth gameplay [Video]. YouTube. https://www.youtube.com/watch?v=7HKPvMOSjPw

Unknown creator. (n.d.). Pygame tutorial - part 13 - health bars [Video]. YouTube. https://www.youtube.com/watch?v=m-XqM41ZlvA

JennEngineer [@jennengineer]. (2024, n.d.). A very simple python game courtesy of pygame #pythonprogramming #techtok #codingtiktok #codingisfun #pygame [Video]. TikTok. https://www.tiktok.com/@jennengineer/video/7378975582127672618

JennEngineer [@jennengineer]. (2024, January 16). This might be the simplest game in python / pygame lol [Video]. TikTok. https://www.tiktok.com/@jennengineer/video/7324788642650574123

Ouali Code [@ouali.code]. (2025, n.d.). Making games with Python pygame [Video]. TikTok. https://www.tiktok.com/@ouali.code/video/7468061900811619590

Thom Code [@thom.code]. (2025, n.d.). Making a game in Python with no experience #gamedev #programming #python #pygame [Video]. TikTok. https://www.tiktok.com/@thom.code/video/7483063173600300310

Tiff in Tech [@tiffintech]. (2022, n.d.). Coding a game using Python and pygame #pygame #python #tech #womeninstem [Video]. TikTok. https://www.tiktok.com/@tiffintech/video/7133989870644579589

CodersLegacy. (2021, November 19). Pygame RPG tutorial - status bar. CodersLegacy. https://coderslegacy.com/python/pygame-rpg-status-bar/

demaisj. (n.d.). Pygame-Transitions: Beautiful & easy transitions for pygame programs [Source code]. GitHub. https://github.com/demaisj/Pygame-Transitions

GameDev Academy. (2023, November 8). Pygame animation tutorial: Complete guide. GameDev Academy. https://gamedevacademy.org/pygame-animation-tutorial-complete-guide/

GeeksforGeeks. (2025). How to create a pop up in pygame with pgu? GeeksforGeeks. https://www.geeksforgeeks.org/python/how-to-create-a-pop-up-in-pygame-with-pgu/

GeeksforGeeks. (2025). Save/load game function in pygame. GeeksforGeeks. https://www.geeksforgeeks.org/python/save-load-game-function-in-pygame/

Inventwithpython.com. (n.d.). Chapter 18 - Animating graphics. Invent With Python. https://inventwithpython.com/invent4thed/chapter18.html

Kwan, I. (2013, April 29). Using PyInstaller to make EXEs from Python scripts (and a 48-hour game design compo). Irwin Kwan. https://irwinkwan.com/2013/04/29/python-executables-pyinstaller-and-a-48-hour-game-design-compo/

MakeUseOf. (2023, July 12). Adding special effects to pygame games: Particle systems and visual enhancements. MakeUseOf. https://www.makeuseof.com/pygame-games-special-effects-particle-systems-visual-enhancements/

Program Arcade Games. (n.d.). Introduction to animation. Program Arcade Games With Python and Pygame. http://programarcadegames.com/index.php?lang=en&chapter=introduction_to_animation

Pygame GUI. (n.d.). Text effects. Pygame GUI Documentation. https://pygame-gui.readthedocs.io/en/latest/text_effects.html

PygameVN. (n.d.). Game state management. PygameVN. https://staff6773.github.io/PygameVN/game_state_management/

Real Python. (2025, February 2). Build a quiz application with Python. Real Python. https://realpython.com/python-quiz-application/

RipTutorial. (n.d.). Drawing and a basic animation. RipTutorial. https://riptutorial.com/pygame/example/17502/drawing-and-a-basic-animation

Tech with Tim. (n.d.). Pygame tutorial - scoring & health bars. Tech with Tim. https://www.techwithtim.net/tutorials/game-development-with-python/pygame-tutorial/scoring-health-bars

Tech with Tim. (n.d.). Pygame animation. Tech with Tim. https://www.techwithtim.net/tutorials/game-development-with-python/pygame-tutorial/pygame-animation
"""