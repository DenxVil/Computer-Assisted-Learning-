"""
Settings Module
===============
App-wide settings stored in memory (no persistence needed).
"""

from dataclasses import dataclass


@dataclass
class AppSettings:
    language: str = "English"
    sound_enabled: bool = True
    fullscreen: bool = False
    animation_speed: float = 1.0   # 0.5x to 2.0x
    graph_style: str = "modern"    # "modern" or "classic"

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen


# Global settings instance
settings = AppSettings()
