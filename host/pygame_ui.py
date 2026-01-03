import pygame
import os
from PIL import Image
from shared.domain.actions import Action


class AnimatedSprite:
    def __init__(self, filepath, size):
        self.frames = []
        self.current_frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_delay = 100
        with Image.open(filepath) as img:
            for i in range(img.n_frames):
                img.seek(i)
                frame_rgba = img.convert("RGBA")
                pygame_surface = pygame.image.fromstring(frame_rgba.tobytes(), frame_rgba.size, "RGBA")
                pygame_surface = pygame.transform.scale(pygame_surface, (size, size))
                self.frames.append(pygame_surface)

    def get_frame(self, flip_x=False):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_delay:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.last_update = now
        frame = self.frames[self.current_frame]
        return pygame.transform.flip(frame, flip_x, False)


class RetroRenderer:
    def __init__(self, screen, grid_size, cell_size, font):
        self.screen = screen
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.font = font
        
        # PATH SETUP
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.ASSETS_DIR = os.path.join(self.BASE_DIR, "assets")

        try:
            self.small_font = pygame.font.Font(os.path.join(self.ASSETS_DIR, "font.ttf"), 12)
        except:
            self.small_font = pygame.font.SysFont("monospace", 12)

        self.hunter_facing_left = False
        self.prey_facing_left = False
        self.SIDEBAR_WIDTH = 350

        # UI Elementi
        self.btn_pause = pygame.Rect(0, 0, 0, 0)
        self.btn_exit = pygame.Rect(0, 0, 0, 0)
        self.btn_reset = pygame.Rect(0, 0, 0, 0)
        
        # Dialog UI
        self.show_reset_dialog = False
        self.dialog_rect = pygame.Rect(0, 0, 400, 200)
        self.btn_confirm = pygame.Rect(0, 0, 0, 0)
        self.btn_cancel = pygame.Rect(0, 0, 0, 0)

        # Slider definicija
        self.slider_rect = pygame.Rect(0, 0, 200, 10)
        self.slider_handle_rect = pygame.Rect(0, 0, 15, 25)
        self.is_dragging_slider = False

        try:
            self.hunter_sprite = AnimatedSprite(os.path.join(self.ASSETS_DIR, "ghost.gif"), cell_size - 4)
            self.prey_sprite = AnimatedSprite(os.path.join(self.ASSETS_DIR, "frog.gif"), cell_size - 4)
            self.ground_img = pygame.image.load(os.path.join(self.ASSETS_DIR, "ground.png")).convert_alpha()
            self.ground_img = pygame.transform.scale(self.ground_img, (cell_size, cell_size))
            self.stone_img = pygame.image.load(os.path.join(self.ASSETS_DIR, "stone.png")).convert_alpha()
            self.stone_img = pygame.transform.scale(self.stone_img, (cell_size, cell_size))
            self.plank_img = pygame.image.load(os.path.join(self.ASSETS_DIR, "plank.png")).convert_alpha()
            self.plank_img = pygame.transform.scale(self.plank_img, (cell_size - 8, cell_size - 8))
            self.logo = pygame.image.load(os.path.join(self.ASSETS_DIR, "logo.png")).convert_alpha()
            w, h = self.logo.get_size()
            scale = 300 / w
            self.logo = pygame.transform.smoothscale(self.logo, (int(w * scale), int(h * scale)))
        except Exception as e:
            print(f"UI Assets Error: {e}")
            self.hunter_sprite = self.prey_sprite = self.logo = self.plank_img = self.ground_img = self.stone_img = None

    def draw_world(self, grid):
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                x, y = c * self.cell_size, r * self.cell_size
                if self.ground_img: self.screen.blit(self.ground_img, (x, y))
                if (r, c) in grid.walls:
                    if self.stone_img: self.screen.blit(self.stone_img, (x, y))
                if grid.is_pallet_active((r, c)):
                    if self.plank_img: self.screen.blit(self.plank_img, (x + 4, y + 4))

    def draw_agents(self, hunter, prey, last_h_action=None, last_p_action=None):
        if last_h_action == Action.LEFT:
            self.hunter_facing_left = True
        elif last_h_action == Action.RIGHT:
            self.hunter_facing_left = False
        if last_p_action == Action.LEFT:
            self.prey_facing_left = True
        elif last_p_action == Action.RIGHT:
            self.prey_facing_left = False
        hr, hc = hunter.position
        if self.hunter_sprite:
            self.screen.blit(self.hunter_sprite.get_frame(self.hunter_facing_left),
                             (hc * self.cell_size + 2, hr * self.cell_size + 2))
        pr, pc = prey.position
        if self.prey_sprite:
            self.screen.blit(self.prey_sprite.get_frame(self.prey_facing_left),
                             (pc * self.cell_size + 2, pr * self.cell_size + 2))

    def draw_sidebar(self, metrics, steps, h_eps, p_eps, logs, simulation_speed, paused):
        x_off = self.grid_size * self.cell_size
        win_height = self.screen.get_height()
        pygame.draw.rect(self.screen, (25, 25, 30), (x_off, 0, self.SIDEBAR_WIDTH, win_height))
        pygame.draw.line(self.screen, (100, 100, 120), (x_off, 0), (x_off, win_height), 2)

        # 1. LOGO
        y = 15
        if self.logo:
            logo_x = x_off + (self.SIDEBAR_WIDTH - self.logo.get_width()) // 2
            self.screen.blit(self.logo, (logo_x, y))
            y += self.logo.get_height() + 10

        # 2. GIF RESULTS
        pygame.draw.line(self.screen, (60, 60, 70), (x_off + 20, y), (x_off + self.SIDEBAR_WIDTH - 20, y), 1)
        y += 10
        if self.hunter_sprite: self.screen.blit(self.hunter_sprite.get_frame(), (x_off + 30, y - 5))
        self.screen.blit(self.font.render(f"HUNTER WINS: {metrics.hunter_wins}", True, (255, 150, 150)),
                         (x_off + 85, y))
        y += 35
        if self.prey_sprite: self.screen.blit(self.prey_sprite.get_frame(), (x_off + 30, y - 5))
        self.screen.blit(self.font.render(f"PREY WINS: {metrics.prey_wins}", True, (150, 255, 150)), (x_off + 85, y))
        y += 45

        # 3. STATISTIKA
        stats = [
            (f"STATUS: {'PAUSED' if paused else 'RUNNING'}", (255, 100, 100) if paused else (100, 255, 100)),
            (f"EPISODES: {metrics.total_episodes}", (255, 255, 255)),
            (f"STEPS: {steps}", (200, 200, 200)),
            (f"H-EPS: {h_eps:.2f} | P-EPS: {p_eps:.2f}", (200, 200, 200)),
            (f"SPEED: {simulation_speed}x", (180, 180, 180)),

        ]
        for text, col in stats:
            self.screen.blit(self.font.render(text, True, col), (x_off + 30, y))
            y += 24

        # 4. SLIDER (Pomjeren malo niže)
        y += 10
        self.slider_rect.topleft = (x_off + 30, y)
        pygame.draw.rect(self.screen, (60, 60, 70), self.slider_rect, border_radius=5)
        # Izračunaj poziciju ručke na osnovu simulation_speed (1 do 100)
        handle_x = self.slider_rect.x + (simulation_speed - 1) / 99 * self.slider_rect.width
        self.slider_handle_rect.center = (handle_x, self.slider_rect.centery)
        pygame.draw.rect(self.screen, (100, 255, 100), self.slider_handle_rect, border_radius=3)

        # 5. GUMBOVI (Dynamic positioning)
        y += 35
        self.btn_reset = pygame.Rect(x_off + 30, y, 290, 35)
        self._draw_button(self.btn_reset, "RESET LEARNING (DELETE DATA)", (255, 80, 80))

        # 6. EVENT LOG (Dynamic positioning)
        y += 45
        pygame.draw.line(self.screen, (60, 60, 70), (x_off + 20, y), (x_off + self.SIDEBAR_WIDTH - 20, y), 1)
        y += 10
        self.screen.blit(self.small_font.render("EVENT LOG:", True, (150, 150, 150)), (x_off + 30, y))
        y += 20
        
        # Calculate remaining space for logs
        remaining_height = win_height - y - 10
        max_logs = max(0, remaining_height // 18)
        
        for i, log in enumerate(logs):
            if i >= max_logs: break
            self.screen.blit(self.small_font.render(log, True, (130, 130, 140)), (x_off + 30, y))
            y += 18

    def draw_reset_dialog(self):
        if not self.show_reset_dialog: return
        
        # Overlay
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Dialog Box
        cx, cy = self.screen.get_width() // 2, self.screen.get_height() // 2
        self.dialog_rect.center = (cx, cy)
        pygame.draw.rect(self.screen, (40, 40, 45), self.dialog_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 80, 80), self.dialog_rect, 2, border_radius=10)
        
        # Text
        msg1 = self.font.render("Are you sure you wanna reset", True, (255, 255, 255))
        msg2 = self.font.render("the Agent learning process?", True, (255, 255, 255))
        msg3 = self.small_font.render("This will DELETE all checkpoints and stats!", True, (255, 100, 100))
        
        self.screen.blit(msg1, msg1.get_rect(center=(cx, cy - 50)))
        self.screen.blit(msg2, msg2.get_rect(center=(cx, cy - 25)))
        self.screen.blit(msg3, msg3.get_rect(center=(cx, cy + 10)))
        
        # Buttons
        self.btn_confirm = pygame.Rect(0, 0, 120, 40)
        self.btn_cancel = pygame.Rect(0, 0, 120, 40)
        self.btn_confirm.bottomleft = (self.dialog_rect.left + 40, self.dialog_rect.bottom - 20)
        self.btn_cancel.bottomright = (self.dialog_rect.right - 40, self.dialog_rect.bottom - 20)
        
        self._draw_button(self.btn_confirm, "YES, RESET", (255, 50, 50), fill=True)
        self._draw_button(self.btn_cancel, "CANCEL", (100, 100, 100), fill=True)

    def _draw_button(self, rect, text, color, fill=False):
        if fill:
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            txt_col = (255, 255, 255)
        else:
            pygame.draw.rect(self.screen, color, rect, 2, border_radius=5)
            txt_col = color
            
        txt_img = self.small_font.render(text, True, txt_col)
        txt_rect = txt_img.get_rect(center=rect.center)
        self.screen.blit(txt_img, txt_rect)