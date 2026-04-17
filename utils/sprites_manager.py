import pygame
import os


class SpriteManager:
    def __init__(self):
        self.sprites = {}
        self.load_all_sprites()

    def load_all_sprites(self):
        """Load all game sprites"""

        # Load house sprite
        self.load_sprite("house", "assets/images/buildings/house.png", (96, 96))

        # You can add more buildings here
        # self.load_sprite("barn", "assets/images/buildings/barn.png", (96, 96))

    def load_sprite(self, name, path, size=None):
        """Load a single sprite"""
        try:
            sprite = pygame.image.load(path).convert_alpha()
            if size:
                sprite = pygame.transform.scale(sprite, size)
            self.sprites[name] = sprite
            print(f"Loaded sprite: {name}")
        except Exception as e:
            print(f"Could not load {name}: {e}")
            # Create fallback colored rectangle
            self.sprites[name] = self.create_fallback(size or (48, 48), (150, 100, 50))

    def create_fallback(self, size, color):
        """Create colored rectangle as fallback"""
        surface = pygame.Surface(size)
        surface.fill(color)
        return surface

    def get_sprite(self, name):
        """Get a sprite by name"""
        return self.sprites.get(name)
