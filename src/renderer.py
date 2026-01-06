"""ANSI escape code parser and pygame renderer."""

import os
import re
import sys
from typing import Tuple, List, Optional, Dict, Set
from pathlib import Path
import pygame


# ANSI escape code patterns - pre-compiled for speed
ANSI_ESCAPE = re.compile(r"\x1b\[([0-9;]*)m")
ANSI_CURSOR_POS = re.compile(r"\x1b\[(\d+);(\d+)H")
ANSI_CLEAR = re.compile(r"\x1b\[2?J")
ANSI_ANY = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

# Type alias for cell data
CellData = Tuple[str, Tuple[int, int, int]]  # (char, color)


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

        # Pre-create background tile for clearing cells
        self._bg_tile = pygame.Surface((self.char_width, self.char_height))
        self._bg_tile.fill(background_color)

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

    def parse_ansi_frame_sparse(self, frame: str, canvas_width: int = 200, canvas_height: int = 100) -> List[Tuple[int, int, str, Tuple[int, int, int]]]:
        """
        Parse ANSI frame into sparse list of non-empty cells.
        Returns list of (row, col, char, color) tuples - much faster than full grid.
        """
        cells = []
        current_color = self.default_fg_color
        cursor_row = 0
        cursor_col = 0

        i = 0
        frame_len = len(frame)
        while i < frame_len:
            char = frame[i]

            # Check for ANSI escape sequence
            if char == "\x1b" and i + 1 < frame_len and frame[i + 1] == "[":
                # Try to match cursor position code first
                pos_match = ANSI_CURSOR_POS.match(frame, i)
                if pos_match:
                    cursor_row = int(pos_match.group(1)) - 1
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
            if char == "\n":
                cursor_row += 1
                cursor_col = 0
                i += 1
                continue

            # Handle carriage return
            if char == "\r":
                cursor_col = 0
                i += 1
                continue

            # Non-space character - add to sparse list
            if char != " " and 0 <= cursor_row < canvas_height and 0 <= cursor_col < canvas_width:
                cells.append((cursor_row, cursor_col, char, current_color))

            cursor_col += 1
            i += 1

        return cells

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

    def parse_to_dict(
        self, frame: str, canvas_width: int, canvas_height: int
    ) -> Dict[Tuple[int, int], CellData]:
        """Parse ANSI frame into dict keyed by (row, col) for delta comparison."""
        cells = self.parse_ansi_frame_sparse(frame, canvas_width, canvas_height)
        return {(row, col): (char, color) for row, col, char, color in cells}

    def render_frame_delta(
        self,
        frame: str,
        surface: pygame.Surface,
        prev_cells: Dict[Tuple[int, int], CellData],
        offset_x: int = 0,
        offset_y: int = 0,
        canvas_width: int = 200,
        canvas_height: int = 100,
    ) -> Dict[Tuple[int, int], CellData]:
        """
        Render only the delta between previous and current frame.
        Returns the current cells dict for use as prev_cells next frame.
        """
        # Parse current frame to dict
        curr_cells = self.parse_to_dict(frame, canvas_width, canvas_height)

        char_w = self.char_width
        char_h = self.char_height
        bg_tile = self._bg_tile

        # Find cells to clear (were in prev, not in curr OR changed)
        # Find cells to draw (new or changed)
        clear_list = []
        draw_list = []

        # Check cells that were previously drawn
        prev_keys = set(prev_cells.keys())
        curr_keys = set(curr_cells.keys())

        # Cells that need to be cleared (no longer present)
        for pos in prev_keys - curr_keys:
            row, col = pos
            px = offset_x + col * char_w
            py = offset_y + row * char_h
            clear_list.append((bg_tile, (px, py)))

        # Cells that are new or changed
        for pos in curr_keys:
            curr_data = curr_cells[pos]
            prev_data = prev_cells.get(pos)

            if prev_data != curr_data:
                # New or changed cell - need to draw
                row, col = pos
                char, color = curr_data
                px = offset_x + col * char_w
                py = offset_y + row * char_h
                # Clear first if there was something different
                if prev_data is not None:
                    clear_list.append((bg_tile, (px, py)))
                draw_list.append((self.get_char_surface(char, color), (px, py)))

        # Batch operations
        if clear_list:
            surface.blits(clear_list, doreturn=False)
        if draw_list:
            surface.blits(draw_list, doreturn=False)

        return curr_cells

    def render_frame(
        self,
        frame: str,
        surface: pygame.Surface,
        offset_x: int = 0,
        offset_y: int = 0,
        canvas_width: int = 200,
        canvas_height: int = 100,
    ) -> None:
        """Render an ANSI frame using sparse parsing + batch blitting."""
        # Parse to sparse list (only non-empty cells)
        cells = self.parse_ansi_frame_sparse(frame, canvas_width, canvas_height)

        if not cells:
            return

        # Build blit list directly from sparse cells
        char_w = self.char_width
        char_h = self.char_height
        blit_list = [
            (self.get_char_surface(char, color), (offset_x + col * char_w, offset_y + row * char_h))
            for row, col, char, color in cells
        ]

        # Batch blit all characters at once
        surface.blits(blit_list, doreturn=False)

    def calculate_text_dimensions(self, text: str) -> Tuple[int, int]:
        """Calculate the pixel dimensions needed to render text."""
        lines = text.split("\n")
        max_width = max(len(line) for line in lines) if lines else 0
        height = len(lines)
        return (max_width * self.char_width, height * self.char_height)

    def clear_cache(self) -> None:
        """Clear the character surface cache."""
        self._char_cache.clear()
