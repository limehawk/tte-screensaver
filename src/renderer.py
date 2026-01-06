"""ANSI escape code parser and pygame renderer."""

import os
import re
import sys
from typing import Tuple, List, Optional
from pathlib import Path
import pygame


# ANSI escape code patterns
ANSI_ESCAPE = re.compile(r"\x1b\[([0-9;]*)m")
ANSI_CURSOR_POS = re.compile(r"\x1b\[(\d+);(\d+)H")
ANSI_CLEAR = re.compile(r"\x1b\[2?J")
ANSI_ANY = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def get_bundled_font_path() -> Optional[Path]:
    """Get path to the bundled font file."""
    # When running from source
    src_dir = Path(__file__).parent.parent
    font_path = src_dir / "assets" / "font.ttf"
    if font_path.exists():
        return font_path

    # When running as frozen executable (PyInstaller)
    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
        font_path = base_path / "assets" / "font.ttf"
        if font_path.exists():
            return font_path

    return None


class ANSIRenderer:
    """Renders ANSI-formatted text to a pygame surface."""

    def __init__(
        self,
        font_size: int = 20,
        background_color: Tuple[int, int, int] = (0, 0, 0),
    ):
        self.font_size = font_size
        self.background_color = background_color
        self.default_fg_color = (255, 255, 255)

        # Initialize font
        pygame.font.init()
        self.font = self._get_monospace_font(font_size)
        self.char_width, self.char_height = self.font.size("M")

        # Character surface cache for performance
        self._char_cache: dict = {}

    def _get_monospace_font(self, size: int) -> pygame.font.Font:
        """Get a monospace font, trying bundled font first."""
        # Try bundled font first (has full Unicode support)
        bundled_font = get_bundled_font_path()
        if bundled_font:
            try:
                return pygame.font.Font(str(bundled_font), size)
            except Exception:
                pass

        # Fallback to system fonts with good Unicode support
        monospace_fonts = [
            "cascadia code",
            "cascadia mono",
            "jetbrains mono",
            "consolas",
            "courier new",
            "courier",
            "liberation mono",
            "dejavu sans mono",
            "monospace",
        ]

        for font_name in monospace_fonts:
            try:
                font = pygame.font.SysFont(font_name, size)
                if font:
                    return font
            except Exception:
                continue

        # Fallback to default font
        return pygame.font.Font(None, size)

    def parse_ansi_frame(self, frame: str, canvas_width: int = 200, canvas_height: int = 100) -> List[List[Tuple[str, Tuple[int, int, int]]]]:
        """
        Parse an ANSI frame into a grid of (character, color) tuples.
        Properly handles cursor positioning escape codes.

        Returns a 2D list where each row is a list of (char, rgb_color) tuples.
        """
        # Initialize grid with spaces
        grid = [[(" ", self.default_fg_color) for _ in range(canvas_width)] for _ in range(canvas_height)]

        current_color = self.default_fg_color
        cursor_row = 0
        cursor_col = 0

        i = 0
        while i < len(frame):
            # Check for ANSI escape sequence
            if frame[i] == "\x1b" and i + 1 < len(frame) and frame[i + 1] == "[":
                # Try to match cursor position code first
                pos_match = ANSI_CURSOR_POS.match(frame, i)
                if pos_match:
                    cursor_row = int(pos_match.group(1)) - 1  # 1-indexed to 0-indexed
                    cursor_col = int(pos_match.group(2)) - 1
                    i = pos_match.end()
                    continue

                # Try to match color code
                color_match = ANSI_ESCAPE.match(frame, i)
                if color_match:
                    codes = color_match.group(1).split(";")
                    current_color = self._parse_color_codes(codes, current_color)
                    i = color_match.end()
                    continue

                # Skip other ANSI codes
                other_match = ANSI_ANY.match(frame, i)
                if other_match:
                    i = other_match.end()
                    continue

            # Handle newline
            if frame[i] == "\n":
                cursor_row += 1
                cursor_col = 0
                i += 1
                continue

            # Handle carriage return
            if frame[i] == "\r":
                cursor_col = 0
                i += 1
                continue

            # Regular character - place at cursor position
            if 0 <= cursor_row < canvas_height and 0 <= cursor_col < canvas_width:
                grid[cursor_row][cursor_col] = (frame[i], current_color)
            cursor_col += 1
            i += 1

        # Trim empty rows from the result
        result = []
        for row in grid:
            # Check if row has any non-space characters
            if any(char != " " for char, _ in row):
                result.append(row)
            elif result:  # Keep empty rows in the middle
                result.append(row)

        return result if result else grid[:1]

    def _parse_color_codes(
        self, codes: List[str], current_color: Tuple[int, int, int]
    ) -> Tuple[int, int, int]:
        """Parse ANSI color codes and return the resulting color."""
        if not codes or codes == [""]:
            return self.default_fg_color

        i = 0
        while i < len(codes):
            try:
                code = int(codes[i])
            except ValueError:
                i += 1
                continue

            if code == 0:
                # Reset
                return self.default_fg_color
            elif code == 38:
                # Foreground color
                if i + 1 < len(codes):
                    try:
                        color_type = int(codes[i + 1])
                    except ValueError:
                        i += 1
                        continue

                    if color_type == 2 and i + 4 < len(codes):
                        # RGB color: 38;2;R;G;B
                        try:
                            r = int(codes[i + 2])
                            g = int(codes[i + 3])
                            b = int(codes[i + 4])
                            return (r, g, b)
                        except (ValueError, IndexError):
                            pass
                        i += 5
                        continue
                    elif color_type == 5 and i + 2 < len(codes):
                        # 256 color: 38;5;N
                        try:
                            color_num = int(codes[i + 2])
                            return self._xterm_to_rgb(color_num)
                        except (ValueError, IndexError):
                            pass
                        i += 3
                        continue
            elif 30 <= code <= 37:
                # Standard foreground colors
                return self._basic_color(code - 30)
            elif 90 <= code <= 97:
                # Bright foreground colors
                return self._basic_color(code - 90, bright=True)

            i += 1

        return current_color

    def _basic_color(self, index: int, bright: bool = False) -> Tuple[int, int, int]:
        """Convert basic ANSI color index to RGB."""
        colors = [
            (0, 0, 0),        # Black
            (170, 0, 0),      # Red
            (0, 170, 0),      # Green
            (170, 85, 0),     # Yellow/Brown
            (0, 0, 170),      # Blue
            (170, 0, 170),    # Magenta
            (0, 170, 170),    # Cyan
            (170, 170, 170),  # White
        ]
        bright_colors = [
            (85, 85, 85),     # Bright Black (Gray)
            (255, 85, 85),    # Bright Red
            (85, 255, 85),    # Bright Green
            (255, 255, 85),   # Bright Yellow
            (85, 85, 255),    # Bright Blue
            (255, 85, 255),   # Bright Magenta
            (85, 255, 255),   # Bright Cyan
            (255, 255, 255),  # Bright White
        ]
        if bright:
            return bright_colors[index] if index < len(bright_colors) else self.default_fg_color
        return colors[index] if index < len(colors) else self.default_fg_color

    def _xterm_to_rgb(self, color_num: int) -> Tuple[int, int, int]:
        """Convert xterm 256 color number to RGB."""
        if color_num < 16:
            # Standard colors
            return self._basic_color(color_num % 8, bright=color_num >= 8)
        elif color_num < 232:
            # 216 color cube (6x6x6)
            color_num -= 16
            r = (color_num // 36) % 6
            g = (color_num // 6) % 6
            b = color_num % 6
            return (
                r * 51 if r else 0,
                g * 51 if g else 0,
                b * 51 if b else 0,
            )
        else:
            # Grayscale
            gray = (color_num - 232) * 10 + 8
            return (gray, gray, gray)

    def get_char_surface(
        self, char: str, color: Tuple[int, int, int]
    ) -> pygame.Surface:
        """Get a cached surface for a character with given color."""
        cache_key = (char, color)
        if cache_key not in self._char_cache:
            self._char_cache[cache_key] = self.font.render(char, True, color)
        return self._char_cache[cache_key]

    def render_frame(
        self,
        frame: str,
        surface: pygame.Surface,
        offset_x: int = 0,
        offset_y: int = 0,
        canvas_width: int = 200,
        canvas_height: int = 100,
    ) -> None:
        """Render an ANSI frame directly to a pygame surface."""
        parsed = self.parse_ansi_frame(frame, canvas_width, canvas_height)

        for row_idx, row in enumerate(parsed):
            y = offset_y + row_idx * self.char_height
            if y > surface.get_height():
                break

            for col_idx, (char, color) in enumerate(row):
                x = offset_x + col_idx * self.char_width
                if x > surface.get_width():
                    break

                if char and char != " ":
                    char_surface = self.get_char_surface(char, color)
                    surface.blit(char_surface, (x, y))

    def calculate_text_dimensions(self, text: str) -> Tuple[int, int]:
        """Calculate the pixel dimensions needed to render text."""
        lines = text.split("\n")
        max_width = max(len(line) for line in lines) if lines else 0
        height = len(lines)
        return (max_width * self.char_width, height * self.char_height)

    def clear_cache(self) -> None:
        """Clear the character surface cache."""
        self._char_cache.clear()
