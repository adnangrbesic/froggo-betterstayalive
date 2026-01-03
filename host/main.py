import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pygame
from shared.application.game_service import GameService
from host.pygame_ui import RetroRenderer

# =====================================================
# CONFIG
# =====================================================
GRID_SIZE, CELL_SIZE = 15, 50
SIDEBAR_WIDTH, MAX_STEPS = 350, 100
WALLS, PALLETS = 35, 12
WINDOW_WIDTH, WINDOW_HEIGHT = GRID_SIZE * CELL_SIZE + SIDEBAR_WIDTH, GRID_SIZE * CELL_SIZE

# =====================================================
# SYSTEM INIT
# =====================================================
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("FROGGO: Better Stay Alive!")
clock = pygame.time.Clock()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
CHECKPOINTS_DIR = os.path.join(PROJECT_ROOT, "checkpoints")

try: FONT = pygame.font.Font(os.path.join(ASSETS_DIR, "font.ttf"), 15)
except: FONT = pygame.font.SysFont("monospace", 15, bold=True)
icon = pygame.image.load(os.path.join(ASSETS_DIR, "favicon.png"))
pygame.display.set_icon(icon)

game_service = GameService(
    grid_size=GRID_SIZE, 
    max_steps=MAX_STEPS,
    hunter_checkpoint=os.path.join(CHECKPOINTS_DIR, "hunter_train.pt"),
    prey_checkpoint=os.path.join(CHECKPOINTS_DIR, "prey_train.pt")
)

renderer = RetroRenderer(screen, GRID_SIZE, CELL_SIZE, FONT)

# =====================================================
# MAIN HOST LOOP
# =====================================================
game_service.start_new_episode(WALLS, PALLETS)
running, paused, simulation_speed = True, False, 1

while running:
    clock.tick(60)
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if renderer.show_reset_dialog:
                if renderer.btn_confirm.collidepoint(mouse_pos):
                    game_service.reset_learning(WALLS, PALLETS)
                    renderer.show_reset_dialog = False
                elif renderer.btn_cancel.collidepoint(mouse_pos):
                    renderer.show_reset_dialog = False
                continue 
            if renderer.btn_pause.collidepoint(mouse_pos): paused = not paused
            elif renderer.btn_exit.collidepoint(mouse_pos): running = False
            elif renderer.btn_reset.collidepoint(mouse_pos): renderer.show_reset_dialog = True
            elif renderer.slider_handle_rect.collidepoint(mouse_pos) or renderer.slider_rect.collidepoint(mouse_pos):
                renderer.is_dragging_slider = True
        if event.type == pygame.MOUSEBUTTONUP: renderer.is_dragging_slider = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: running = False
            if event.key == pygame.K_SPACE: paused = not paused

    if renderer.is_dragging_slider:
        rel_x = max(0, min(renderer.slider_rect.width, mouse_pos[0] - renderer.slider_rect.x))
        simulation_speed = int(1 + (rel_x / renderer.slider_rect.width) * 99)

    h_res, p_res = game_service.update(simulation_speed, paused, WALLS, PALLETS)

    screen.fill((20, 20, 25))
    renderer.draw_world(game_service.grid)
    renderer.draw_agents(game_service.hunter, game_service.prey,
                         last_h_action=h_res.action if h_res else None,
                         last_p_action=p_res.action if p_res else None)
    
    renderer.draw_sidebar(
        game_service.metrics, 
        game_service.episode_service.episode.steps, 
        game_service.h_trainer.epsilon,
        game_service.p_trainer.epsilon, 
        game_service.logger.get_logs(), 
        simulation_speed, 
        paused
    )
    
    renderer.draw_reset_dialog()
    pygame.display.flip()

pygame.quit()