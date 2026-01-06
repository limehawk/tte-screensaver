"""Configuration management for tte-screensaver."""

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Tuple


# Default effects to cycle through - all available effects
DEFAULT_EFFECTS = [
    "Beams",
    "BinaryPath",
    "Blackhole",
    "BouncyBalls",
    "Bubbles",
    "Burn",
    "ColorShift",
    "Crumble",
    "Decrypt",
    "ErrorCorrect",
    "Expand",
    "Fireworks",
    "Highlight",
    "LaserEtch",
    "Matrix",
    "MiddleOut",
    "OrbittingVolley",
    "Overflow",
    "Pour",
    "Print",
    "Rain",
    "RandomSequence",
    "Rings",
    "Scattered",
    "Slice",
    "Slide",
    "Spotlights",
    "Spray",
    "Swarm",
    "Sweep",
    "SynthGrid",
    "Unstable",
    "VHSTape",
    "Waves",
    "Wipe",
]

DEFAULT_ASCII_ART = r"""
██╗     ██╗███╗   ███╗███████╗██╗  ██╗ █████╗ ██╗    ██╗██╗  ██╗
██║     ██║████╗ ████║██╔════╝██║  ██║██╔══██╗██║    ██║██║ ██╔╝
██║     ██║██╔████╔██║█████╗  ███████║███████║██║ █╗ ██║█████╔╝
██║     ██║██║╚██╔╝██║██╔══╝  ██╔══██║██╔══██║██║███╗██║██╔═██╗
███████╗██║██║ ╚═╝ ██║███████╗██║  ██║██║  ██║╚███╔███╔╝██║  ██╗
╚══════╝╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝  ╚═╝
""".strip()


@dataclass
class Config:
    """Screensaver configuration."""

    ascii_art: str = DEFAULT_ASCII_ART
    enabled_effects: List[str] = field(default_factory=lambda: DEFAULT_EFFECTS.copy())
    font_size: int = 18  # Match Omarchy
    background_color: Tuple[int, int, int] = (0, 0, 0)
    target_fps: int = 120  # Match Omarchy

    def to_dict(self) -> dict:
        """Convert config to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """Create config from dictionary."""
        # Handle tuple conversion for background_color
        if "background_color" in data and isinstance(data["background_color"], list):
            data["background_color"] = tuple(data["background_color"])
        return cls(**data)


def get_config_path() -> Path:
    """Get the configuration file path in AppData."""
    if os.name == "nt":
        # Windows: use APPDATA
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        config_dir = Path(appdata) / "tte-screensaver"
    else:
        # Linux/Mac: use ~/.config
        config_dir = Path.home() / ".config" / "tte-screensaver"

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


def load_config() -> Config:
    """Load configuration from file, or return defaults if not found."""
    config_path = get_config_path()

    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Config.from_dict(data)
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            print(f"Warning: Could not load config ({e}), using defaults")
            return Config()

    return Config()


def save_config(config: Config) -> None:
    """Save configuration to file."""
    config_path = get_config_path()

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, indent=2)


def get_default_ascii_path() -> Path:
    """Get path to the default ASCII art file."""
    # When running from source
    src_dir = Path(__file__).parent.parent
    assets_path = src_dir / "assets" / "default_ascii.txt"

    if assets_path.exists():
        return assets_path

    # When running as frozen executable
    import sys
    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
        return base_path / "assets" / "default_ascii.txt"

    return assets_path
