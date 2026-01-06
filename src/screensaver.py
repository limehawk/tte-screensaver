"""Main screensaver pygame loop."""

import os
import sys
import pygame
from typing import Optional, Tuple, List

from .config import Config, load_config
from .renderer import ANSIRenderer
from .effects import EffectManager


def get_virtual_desktop_size() -> Tuple[int, int, int, int]:
    """
    Get the virtual desktop bounds (covers all monitors).
    Returns (x, y, width, height) where x,y is the top-left corner.
    """
    try:
        # Try using ctypes to get virtual screen metrics (Windows)
        import ctypes
        user32 = ctypes.windll.user32
        # SM_XVIRTUALSCREEN = 76, SM_YVIRTUALSCREEN = 77
        # SM_CXVIRTUALSCREEN = 78, SM_CYVIRTUALSCREEN = 79
        x = user32.GetSystemMetrics(76)
        y = user32.GetSystemMetrics(77)
        width = user32.GetSystemMetrics(78)
        height = user32.GetSystemMetrics(79)
        return (x, y, width, height)
    except Exception:
        pass

    # Fallback: use pygame's display info
    pygame.display.init()
    info = pygame.display.Info()
    return (0, 0, info.current_w, info.current_h)


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
            # Get virtual desktop size (spans all monitors)
            vx, vy, vw, vh = get_virtual_desktop_size()
            screen_size = (vw, vh)

            # Position window at virtual desktop origin
            os.environ['SDL_VIDEO_WINDOW_POS'] = f"{vx},{vy}"

            # Create borderless fullscreen window spanning all monitors
            self.screen = pygame.display.set_mode(
                screen_size,
                pygame.NOFRAME | pygame.FULLSCREEN
            )
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
            self._calculate_canvas_size(screen_size)  # Creates renderer

            # Calculate canvas size based on ASCII art dimensions
            lines = self.config.ascii_art.split("\n")
            art_width = max(len(line) for line in lines) if lines else 80
            art_height = len(lines)

            # Add some padding for effect animations
            self.canvas_width = art_width + 20
            self.canvas_height = art_height + 10

            # Initialize effect manager - no timeout, effects run to completion
            self.effect_manager = EffectManager(
                text=self.config.ascii_art,
                enabled_effects=self.config.enabled_effects,
                effect_duration=0,  # 0 = no timeout, only switch on completion
                canvas_width=self.canvas_width,
                canvas_height=self.canvas_height,
            )

            offset = self._calculate_text_offset(screen_size)
            self.running = True

            while self.running:
                # Handle events
                if not self._handle_events():
                    self.running = False
                    break

                # Get next frame
                frame = self.effect_manager.get_next_frame()
                if frame is None:
                    # Effect completed, switch to next
                    self.effect_manager.switch_to_next_effect()
                    if self.renderer:
                        self.renderer.clear_cache()
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
                        canvas_width=self.canvas_width,
                        canvas_height=self.canvas_height,
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
