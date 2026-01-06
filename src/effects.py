"""Effect management and cycling for tte-screensaver."""

import random
from typing import Iterator, Optional, Dict, Type, List
from dataclasses import dataclass

# Import all available TTE effects
from terminaltexteffects.effects.effect_beams import Beams
from terminaltexteffects.effects.effect_binarypath import BinaryPath
from terminaltexteffects.effects.effect_blackhole import Blackhole
from terminaltexteffects.effects.effect_bouncyballs import BouncyBalls
from terminaltexteffects.effects.effect_bubbles import Bubbles
from terminaltexteffects.effects.effect_burn import Burn
from terminaltexteffects.effects.effect_colorshift import ColorShift
from terminaltexteffects.effects.effect_crumble import Crumble
from terminaltexteffects.effects.effect_decrypt import Decrypt
from terminaltexteffects.effects.effect_errorcorrect import ErrorCorrect
from terminaltexteffects.effects.effect_expand import Expand
from terminaltexteffects.effects.effect_fireworks import Fireworks
from terminaltexteffects.effects.effect_highlight import Highlight
from terminaltexteffects.effects.effect_laseretch import LaserEtch
from terminaltexteffects.effects.effect_matrix import Matrix
from terminaltexteffects.effects.effect_middleout import MiddleOut
from terminaltexteffects.effects.effect_orbittingvolley import OrbittingVolley
from terminaltexteffects.effects.effect_overflow import Overflow
from terminaltexteffects.effects.effect_pour import Pour
from terminaltexteffects.effects.effect_print import Print
from terminaltexteffects.effects.effect_rain import Rain
from terminaltexteffects.effects.effect_random_sequence import RandomSequence
from terminaltexteffects.effects.effect_rings import Rings
from terminaltexteffects.effects.effect_scattered import Scattered
from terminaltexteffects.effects.effect_slice import Slice
from terminaltexteffects.effects.effect_slide import Slide
from terminaltexteffects.effects.effect_spotlights import Spotlights
from terminaltexteffects.effects.effect_spray import Spray
from terminaltexteffects.effects.effect_swarm import Swarm
from terminaltexteffects.effects.effect_sweep import Sweep
from terminaltexteffects.effects.effect_synthgrid import SynthGrid
from terminaltexteffects.effects.effect_unstable import Unstable
from terminaltexteffects.effects.effect_vhstape import VHSTape
from terminaltexteffects.effects.effect_waves import Waves
from terminaltexteffects.effects.effect_wipe import Wipe


# Map of effect names to their classes
AVAILABLE_EFFECTS: Dict[str, Type] = {
    "Beams": Beams,
    "BinaryPath": BinaryPath,
    "Blackhole": Blackhole,
    "BouncyBalls": BouncyBalls,
    "Bubbles": Bubbles,
    "Burn": Burn,
    "ColorShift": ColorShift,
    "Crumble": Crumble,
    "Decrypt": Decrypt,
    "ErrorCorrect": ErrorCorrect,
    "Expand": Expand,
    "Fireworks": Fireworks,
    "Highlight": Highlight,
    "LaserEtch": LaserEtch,
    "Matrix": Matrix,
    "MiddleOut": MiddleOut,
    "OrbittingVolley": OrbittingVolley,
    "Overflow": Overflow,
    "Pour": Pour,
    "Print": Print,
    "Rain": Rain,
    "RandomSequence": RandomSequence,
    "Rings": Rings,
    "Scattered": Scattered,
    "Slice": Slice,
    "Slide": Slide,
    "Spotlights": Spotlights,
    "Spray": Spray,
    "Swarm": Swarm,
    "Sweep": Sweep,
    "SynthGrid": SynthGrid,
    "Unstable": Unstable,
    "VHSTape": VHSTape,
    "Waves": Waves,
    "Wipe": Wipe,
}


def get_available_effect_names() -> List[str]:
    """Return a list of all available effect names."""
    return sorted(AVAILABLE_EFFECTS.keys())


@dataclass
class EffectState:
    """Tracks the current state of effect cycling."""

    current_effect_index: int = 0
    current_iterator: Optional[Iterator[str]] = None
    effect_completed: bool = False


class EffectManager:
    """Manages effect creation and cycling."""

    def __init__(
        self,
        text: str,
        enabled_effects: List[str],
        canvas_width: int = 80,
        canvas_height: int = 24,
    ):
        """
        Initialize the effect manager.

        Args:
            text: The ASCII art text to animate
            enabled_effects: List of effect names to cycle through
            canvas_width: Width of the terminal canvas in characters
            canvas_height: Height of the terminal canvas in characters
        """
        self.text = text
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height

        # Filter enabled effects to only valid ones
        self.enabled_effects = [
            name for name in enabled_effects if name in AVAILABLE_EFFECTS
        ]
        if not self.enabled_effects:
            # Fallback to some defaults if no valid effects
            self.enabled_effects = ["Matrix", "Rain", "Decrypt"]

        # Shuffle effects for random order
        random.shuffle(self.enabled_effects)

        self.state = EffectState()
        self._create_effect()

    def _create_effect(self) -> None:
        """Create a new effect instance for the current effect index."""
        effect_name = self.enabled_effects[self.state.current_effect_index]
        effect_class = AVAILABLE_EFFECTS[effect_name]

        # Create the effect instance
        effect = effect_class(self.text)

        # Configure for external rendering (GUI mode)
        # ignore_terminal_dimensions allows rendering outside terminal constraints
        effect.terminal_config.ignore_terminal_dimensions = True

        # Use full screen canvas dimensions for effects like Matrix/Rain
        # to render across the entire display, not just around the text
        effect.terminal_config.canvas_width = self.canvas_width
        effect.terminal_config.canvas_height = self.canvas_height

        # Center the text within the canvas (like Omarchy's --anchor-text c)
        effect.terminal_config.anchor_text = "c"  # Center text
        effect.terminal_config.anchor_canvas = "c"  # Center canvas

        # Set frame rate to match our target
        effect.terminal_config.frame_rate = 0  # 0 = unlimited, we control timing

        # Get the iterator
        self.state.current_iterator = iter(effect)
        self.state.effect_completed = False

    def get_current_effect_name(self) -> str:
        """Get the name of the currently active effect."""
        return self.enabled_effects[self.state.current_effect_index]

    def should_switch_effect(self) -> bool:
        """Check if it's time to switch to the next effect."""
        # Only switch when effect completes
        return self.state.effect_completed

    def switch_to_next_effect(self) -> None:
        """Switch to a random different effect."""
        if len(self.enabled_effects) > 1:
            # Pick a random effect that's different from current
            current = self.state.current_effect_index
            choices = [i for i in range(len(self.enabled_effects)) if i != current]
            self.state.current_effect_index = random.choice(choices)
        self._create_effect()

    def get_next_frame(self) -> Optional[str]:
        """
        Get the next frame from the current effect.

        Returns None if the effect has completed and we should switch.
        """
        if self.state.current_iterator is None:
            self._create_effect()

        try:
            frame = next(self.state.current_iterator)
            return frame
        except StopIteration:
            self.state.effect_completed = True
            return None

    def update_text(self, new_text: str) -> None:
        """Update the text and restart the current effect."""
        self.text = new_text
        self._create_effect()

    def update_canvas_size(self, width: int, height: int) -> None:
        """Update the canvas size and restart the current effect."""
        self.canvas_width = width
        self.canvas_height = height
        self._create_effect()
