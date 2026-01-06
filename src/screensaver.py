"""Main screensaver pygame loop."""

import sys
import pygame
from typing import Optional, Tuple

from .config import Config, load_config
from .renderer import ANSIRenderer
from .effects import EffectManager


class Screensaver:
    """Main screensaver application."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize the screensaver."""
        self.config = config or load_config()
        self.running = False
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None
        self.renderer: Optional[ANSIRenderer] = None
        self.effect_manager: Optional[EffectManager] = None

        # Track mouse position for exit detection
        self.initial_mouse_pos: Optional[Tuple[int, int]] = None
        self.mouse_move_threshold = 10  # pixels

    def _init_pygame(self, fullscreen: bool = True) -> Tuple[int, int]:
        """Initialize pygame and create the display."""
        pygame.init()
        pygame.mouse.set_visible(False)

        if fullscreen:
            # Get display info for fullscreen
            info = pygame.display.Info()
            screen_size = (info.current_w, info.current_h)
            self.screen = pygame.display.set_mode(screen_size, pygame.FULLSCREEN)
        else:
            # Windowed mode for testing
            screen_size = (1280, 720)
            self.screen = pygame.display.set_mode(screen_size)

        pygame.display.set_caption("TTE Screensaver")
        self.clock = pygame.time.Clock()

        return screen_size

    def _calculate_canvas_size(self, screen_size: Tuple[int, int]) -> Tuple[int, int]:
        """Calculate the terminal canvas size based on screen and font size."""
        screen_width, screen_height = screen_size

        # Create renderer to get char dimensions
        self.renderer = ANSIRenderer(
            font_size=self.config.font_size,
            background_color=self.config.background_color,
        )

        # Calculate how many characters fit on screen
        canvas_width = screen_width // self.renderer.char_width
        canvas_height = screen_height // self.renderer.char_height

        return (canvas_width, canvas_height)

    def _calculate_text_offset(self, screen_size: Tuple[int, int]) -> Tuple[int, int]:
        """Calculate offset to center the text on screen."""
        if self.renderer is None:
            return (0, 0)

        text_width, text_height = self.renderer.calculate_text_dimensions(
            self.config.ascii_art
        )
        screen_width, screen_height = screen_size

        offset_x = max(0, (screen_width - text_width) // 2)
        offset_y = max(0, (screen_height - text_height) // 2)

        return (offset_x, offset_y)

    def _handle_events(self) -> bool:
        """
        Handle pygame events.

        Returns False if the screensaver should exit.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                # Any key press exits
                return False

            if event.type == pygame.MOUSEBUTTONDOWN:
                # Any mouse click exits
                return False

            if event.type == pygame.MOUSEMOTION:
                # Check for significant mouse movement
                current_pos = pygame.mouse.get_pos()
                if self.initial_mouse_pos is None:
                    self.initial_mouse_pos = current_pos
                else:
                    dx = abs(current_pos[0] - self.initial_mouse_pos[0])
                    dy = abs(current_pos[1] - self.initial_mouse_pos[1])
                    if dx > self.mouse_move_threshold or dy > self.mouse_move_threshold:
                        return False

        return True

    def run(self, fullscreen: bool = True) -> None:
        """Run the screensaver main loop."""
        try:
            screen_size = self._init_pygame(fullscreen)
            canvas_width, canvas_height = self._calculate_canvas_size(screen_size)

            # Initialize effect manager
            self.effect_manager = EffectManager(
                text=self.config.ascii_art,
                enabled_effects=self.config.enabled_effects,
                effect_duration=self.config.effect_duration,
                canvas_width=canvas_width,
                canvas_height=canvas_height,
            )

            offset = self._calculate_text_offset(screen_size)
            self.running = True

            while self.running:
                # Handle events
                if not self._handle_events():
                    self.running = False
                    break

                # Check if we should switch effects
                if self.effect_manager.should_switch_effect():
                    self.effect_manager.switch_to_next_effect()
                    # Clear cache when switching effects
                    if self.renderer:
                        self.renderer.clear_cache()

                # Get next frame
                frame = self.effect_manager.get_next_frame()
                if frame is None:
                    # Effect completed, switch immediately
                    self.effect_manager.switch_to_next_effect()
                    frame = self.effect_manager.get_next_frame()

                # Clear screen
                self.screen.fill(self.config.background_color)

                # Render frame
                if frame and self.renderer:
                    self.renderer.render_frame(
                        frame,
                        self.screen,
                        offset_x=offset[0],
                        offset_y=offset[1],
                    )

                # Update display
                pygame.display.flip()

                # Cap frame rate
                self.clock.tick(self.config.target_fps)

        except Exception as e:
            print(f"Screensaver error: {e}", file=sys.stderr)
            raise
        finally:
            pygame.quit()


def run_screensaver(fullscreen: bool = True, config: Optional[Config] = None) -> None:
    """Convenience function to run the screensaver."""
    screensaver = Screensaver(config=config)
    screensaver.run(fullscreen=fullscreen)
