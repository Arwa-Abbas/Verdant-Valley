import pygame

# Window & Grid
WINDOW_TITLE = "Verdant Valley"
SCREEN_W, SCREEN_H = 1280, 800
FPS = 60
TILE_SIZE = 48
GRID_COLS, GRID_ROWS = 18, 14
SIDEBAR_W = 320
GRID_OFFSET_X, GRID_OFFSET_Y = 0, 80  # Increased top offset for better HUD

# Enhanced Color Palette
C_BG_DARK = (18, 26, 18)
C_BG_MID = (28, 40, 28)
C_BG_PANEL = (22, 33, 22)
C_PANEL_BORD = (80, 120, 80)
C_HUD_BG = (14, 20, 14)
C_HUD_BORD = (60, 100, 60)

# Text Colors
C_TEXT_MAIN = (240, 255, 230)
C_TEXT_DIM = (160, 190, 150)
C_TEXT_GOLD = (255, 215, 100)
C_TEXT_WARN = (255, 120, 60)
C_TEXT_SUCCESS = (100, 255, 100)
C_TEXT_TITLE = (255, 220, 150)

# Agent Colors (more vibrant)
C_FARMER = (100, 200, 80)
C_GUARD = (220, 80, 60)
C_ANIMAL = (240, 180, 60)
C_GRASS = (80, 160, 60)

# UI Element Colors
C_BUTTON_NORMAL = (40, 70, 40)
C_BUTTON_HOVER = (60, 100, 60)
C_BUTTON_PRESSED = (30, 50, 30)
C_PROGRESS_BG = (30, 40, 30)
C_PROGRESS_FILL = (100, 200, 80)

# Path Colors
C_PATH_FARMER = (100, 255, 100)
C_PATH_GUARD = (255, 100, 80)
C_PATH_ANIMAL = (255, 200, 100)
C_EXPLORED = (255, 255, 100, 60)

# Tile Types & Costs
TILE_GRASS, TILE_DIRT, TILE_STONE, TILE_MUD, TILE_WATER, TILE_FIELD = 0, 1, 2, 3, 4, 5
TILE_COST = {
    TILE_GRASS: 1.0,
    TILE_DIRT: 1.0,
    TILE_STONE: 0.5,
    TILE_MUD: 3.0,
    TILE_WATER: 999,
    TILE_FIELD: 1.0,
}

# Enhanced Tile Colors with gradients
TILE_COLOR = {
    TILE_GRASS: (56, 95, 40),
    TILE_DIRT: (94, 68, 42),
    TILE_STONE: (100, 100, 110),
    TILE_MUD: (85, 62, 40),
    TILE_WATER: (40, 90, 160),
    TILE_FIELD: (101, 67, 33),
}

# Crops
CROP_NONE, CROP_WHEAT, CROP_SUNFLOWER, CROP_CORN = 0, 1, 2, 3
CROP_NAMES = {0: "Empty", 1: "Wheat", 2: "Sunflower", 3: "Corn"}
CROP_COLOR = {0: (70, 55, 30), 1: (230, 200, 60), 2: (255, 180, 0), 3: (180, 220, 60)}
CROP_VALUE = {0: 0, 1: 10, 2: 20, 3: 15}

# Game States
STATE_LOADING, STATE_MENU, STATE_CSP_VIZ, STATE_PLAYING = (
    "loading",
    "menu",
    "csp_viz",
    "playing",
)
STATE_PAUSED, STATE_GA_VIZ, STATE_GAMEOVER = "paused", "ga_viz", "gameover"

# Seasons
SEASONS = ["🌱 Spring", "☀️ Summer", "🍂 Autumn", "❄️ Winter"]
SEASON_DURATION = 30 * FPS

# Font Sizes
FONT_HUGE, FONT_TITLE, FONT_LARGE, FONT_MEDIUM, FONT_SMALL, FONT_TINY = (
    72,
    48,
    28,
    20,
    15,
    12,
)

# Try to use a nicer system font
FONT_NAME = "Arial"  # Change to "Segoe UI", "Helvetica", or "Consolas" based on your OS
