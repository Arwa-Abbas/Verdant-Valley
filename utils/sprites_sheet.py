import pygame
import json


class SpriteSheet:
    def __init__(self, filename):
        """Load a sprite sheet"""
        try:
            self.sheet = pygame.image.load(filename).convert_alpha()
            print(
                f"Loaded sprite sheet: {filename} ({self.sheet.get_width()}x{self.sheet.get_height()})"
            )
        except pygame.error:
            print(f"Could not load {filename}")
            self.sheet = None

    def get_sprite(self, x, y, width, height):
        """Extract a single sprite from the sheet"""
        if not self.sheet:
            return None

        sprite = pygame.Surface((width, height), pygame.SRCALPHA)
        sprite.blit(self.sheet, (0, 0), (x, y, width, height))
        return sprite

    def get_sprites_grid(
        self, rows, cols, sprite_width, sprite_height, margin=0, spacing=0
    ):
        """Extract a grid of sprites"""
        sprites = []
        x = margin
        y = margin

        for row in range(rows):
            row_sprites = []
            for col in range(cols):
                sprite = self.get_sprite(x, y, sprite_width, sprite_height)
                if sprite:
                    row_sprites.append(sprite)
                x += sprite_width + spacing
            if row_sprites:
                sprites.append(row_sprites)
            x = margin
            y += sprite_height + spacing

        return sprites

    def load_from_config(self, config_file):
        """Load sprite positions from JSON config"""
        with open(config_file, "r") as f:
            config = json.load(f)

        sprites = {}
        for name, data in config.items():
            sprites[name] = self.get_sprite(
                data["x"], data["y"], data["width"], data["height"]
            )
        return sprites
