"""Main screensaver pygame loop."""

import os
import sys
import random
import pygame
from dataclasses import dataclass
from typing import Optional, Tuple, List

from .config import Config, load_config
from .renderer import ANSIRenderer
from .effects import EffectManager


@dataclass
class MonitorInfo:
    """Information about a single monitor."""
    x: int  # Position relative to virtual desktop
    y: int
    width: int
    height: int


def get_virtual_desktop_size() -> Tuple[int, int, int, int]:
    """
    Get the virtual desktop bounds (covers all monitors).
    Returns (x, y, width, height) where x,y is the top-left corner.
    """
    try:
        import ctypes
        user32 = ctypes.windll.user32
        x = user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
        y = user32.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
        width = user32.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
        height = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
        return (x, y, width, height)
    except Exception:
        pass

    pygame.display.init()
    info = pygame.display.Info()
    return (0, 0, info.current_w, info.current_h)


def get_monitors() -> List[MonitorInfo]:
    """
    Get information about all connected monitors.
    Returns list of MonitorInfo with position and size.
    """
    monitors = []

    try:
        import ctypes
        from ctypes import wintypes

        # Define the callback type
        MONITORENUMPROC = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.POINTER(wintypes.RECT),
            ctypes.c_double
        )

        def monitor_enum_callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
            rect = lprcMonitor.contents
            monitors.append(MonitorInfo(
                x=rect.left,
                y=rect.top,
                width=rect.right - rect.left,
                height=rect.bottom - rect.top
            ))
            return True

        # Enumerate monitors
        ctypes.windll.user32.EnumDisplayMonitors(
            None, None,
            MONITORENUMPROC(monitor_enum_callback),
            0
        )

        if monitors:
            return monitors
    except Exception as e:
        print(f"Monitor enumeration failed: {e}", file=sys.stderr)

    # Fallback: single monitor
    vx, vy, vw, vh = get_virtual_desktop_size()
    return [MonitorInfo(x=vx, y=vy, width=vw, height=vh)]


class MonitorEffect:
    """Manages effect rendering for a single monitor."""

    def __init__(
        self,
        monitor: MonitorInfo,
        config: Config,
        renderer: ANSIRenderer,
        virtual_origin: Tuple[int, int],
        start_index: int = 0,
    ):
        self.monitor = monitor
        self.config = config
        self.renderer = renderer

        # Calculate position relative to pygame window (which starts at virtual origin)
        self.offset_x = monitor.x - virtual_origin[0]
        self.offset_y = monitor.y - virtual_origin[1]

        # Calculate canvas size for this monitor
        self.canvas_width = monitor.width // renderer.char_width
        self.canvas_height = monitor.height // renderer.char_height

        # Create effect manager for this monitor with unique starting effect
        self.effect_manager = EffectManager(
            text=config.ascii_art,
            enabled_effects=config.enabled_effects,
            canvas_width=self.canvas_width,
            canvas_height=self.canvas_height,
            start_index=start_index,
        )

    def update_and_render(self, surface: pygame.Surface) -> None:
        """Get next frame and render to the surface."""
        frame = self.effect_manager.get_next_frame()

        if frame is None:
            # Effect completed, switch to next random effect
            self.effect_manager.switch_to_next_effect()
            # Don't clear cache - it's keyed by (char, color) and still valid
            frame = self.effect_manager.get_next_frame()

        if frame:
            self.renderer.render_frame(
                frame,
                surface,
                offset_x=self.offset_x,
                offset_y=self.offset_y,
                canvas_width=self.canvas_width,
                canvas_height=self.canvas_height,
            )


class Screensaver:
    """Main screensaver application."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize the screensaver."""
        self.config = config or load_config()
        self.running = False
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None
        self.renderer: Optional[ANSIRenderer] = None
        self.monitor_effects: List[MonitorEffect] = []

        # Track mouse position for exit detection
        self.initial_mouse_pos: Optional[Tuple[int, int]] = None
        self.mouse_move_threshold = 10

    def _init_pygame(self, fullscreen: bool = True) -> Tuple[int, int]:
        """Initialize pygame and create the display."""
        if fullscreen:
            vx, vy, vw, vh = get_virtual_desktop_size()
            screen_size = (vw, vh)

            os.environ['SDL_VIDEO_WINDOW_POS'] = f"{vx},{vy}"

            pygame.init()
            pygame.mouse.set_visible(False)

            self.screen = pygame.display.set_mode(screen_size, pygame.NOFRAME)

            # Make window topmost
            try:
                import ctypes
                hwnd = pygame.display.get_wm_info()['window']
                ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 1 | 2)
            except Exception:
                pass
        else:
            pygame.init()
            pygame.mouse.set_visible(False)
            screen_size = (1280, 720)
            self.screen = pygame.display.set_mode(screen_size)

        pygame.display.set_caption("TTE Screensaver")
        self.clock = pygame.time.Clock()

        return screen_size

    def _handle_events(self) -> bool:
        """Handle pygame events. Returns False if should exit."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                return False

            if event.type == pygame.MOUSEBUTTONDOWN:
                return False

            if event.type == pygame.MOUSEMOTION:
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

            # Create renderer
            self.renderer = ANSIRenderer(
                font_size=self.config.font_size,
                background_color=self.config.background_color,
            )

            # Get virtual desktop origin for coordinate conversion
            vx, vy, _, _ = get_virtual_desktop_size()
            virtual_origin = (vx, vy)

            # Get all monitors and create an effect manager for each
            if fullscreen:
                monitors = get_monitors()
            else:
                # Single "monitor" for windowed mode
                monitors = [MonitorInfo(x=0, y=0, width=screen_size[0], height=screen_size[1])]

            print(f"Detected {len(monitors)} monitor(s)", file=sys.stderr)
            for i, m in enumerate(monitors):
                print(f"  Monitor {i+1}: {m.width}x{m.height} at ({m.x}, {m.y})", file=sys.stderr)

            # Create independent effect for each monitor with different starting effects
            # Spread start indices apart so monitors don't show same effect
            num_effects = len(self.config.enabled_effects)
            self.monitor_effects = [
                MonitorEffect(
                    monitor, self.config, self.renderer, virtual_origin,
                    start_index=(i * num_effects // len(monitors)) + random.randint(0, 5)
                )
                for i, monitor in enumerate(monitors)
            ]

            self.running = True

            while self.running:
                if not self._handle_events():
                    self.running = False
                    break

                # Clear screen
                self.screen.fill(self.config.background_color)

                # Render each monitor's effect independently
                for monitor_effect in self.monitor_effects:
                    monitor_effect.update_and_render(self.screen)

                pygame.display.flip()
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
