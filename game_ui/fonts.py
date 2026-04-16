"""
Font management with better font support
"""

import pygame
import os


class FontCache:
    _cache = {}

    @classmethod
    def get(cls, size, bold=False, italic=False):
        key = (size, bold, italic)
        if key not in cls._cache:
            # Try different font options
            font_paths = [
                None,  # Default pygame font
                "Arial.ttf",
                "arial.ttf",
                "segoeui.ttf",
                "Consolas.ttf",
                "DejaVuSans.ttf",
            ]

            font = None
            for font_path in font_paths:
                try:
                    if font_path:
                        font = pygame.font.Font(font_path, size)
                    else:
                        font = pygame.font.Font(None, size)

                    # Apply bold/italic if needed
                    if bold and hasattr(font, "set_bold"):
                        font.set_bold(True)
                    if italic and hasattr(font, "set_italic"):
                        font.set_italic(True)

                    if font:
                        break
                except:
                    continue

            if not font:
                # Fallback to system font
                font = pygame.font.SysFont("monospace", size, bold=bold, italic=italic)

            cls._cache[key] = font

        return cls._cache[key]

    @classmethod
    def clear(cls):
        cls._cache.clear()
