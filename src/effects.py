"""Effect management and cycling for tte-screensaver."""

import random
import threading
from typing import Iterator, Optional, Dict, Type, List

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


class EffectManager:
    """Manages effect creation and cycling with background pre-loading."""

    def __init__(
        self,
        text: str,
        enabled_effects: List[str],
        canvas_width: int = 80,
        canvas_height: int = 24,
        start_index: Optional[int] = None,
    ):
        self.text = text
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height

        # Filter enabled effects to only valid ones
        self.enabled_effects = [
            name for name in enabled_effects if name in AVAILABLE_EFFECTS
        ]
        if not self.enabled_effects:
            self.enabled_effects = ["Matrix", "Rain", "Decrypt"]

        # Don't shuffle - use truly random selection each time
        # This prevents monitors from syncing up

        # Start at a random index (or specified one for diversity across monitors)
        if start_index is not None:
            self._current_index = start_index % len(self.enabled_effects)
        else:
            self._current_index = random.randint(0, len(self.enabled_effects) - 1)

        self._current_iterator: Optional[Iterator[str]] = None
        self._next_iterator: Optional[Iterator[str]] = None
        self._next_index: Optional[int] = None
        self._effect_completed = False
        self._preload_lock = threading.Lock()
        self._preload_ready = threading.Event()

        # Create first effect (blocking - need it now)
        self._current_iterator = self._create_effect_iterator(self._current_index)
        # Start background pre-load of next effect
        self._start_background_preload()

    def _create_effect_iterator(self, index: int) -> Iterator[str]:
        """Create an effect iterator for the given index."""
        effect_name = self.enabled_effects[index]
        effect_class = AVAILABLE_EFFECTS[effect_name]

        effect = effect_class(self.text)
        effect.terminal_config.ignore_terminal_dimensions = True
        effect.terminal_config.canvas_width = self.canvas_width
        effect.terminal_config.canvas_height = self.canvas_height
        effect.terminal_config.anchor_text = "c"
        effect.terminal_config.frame_rate = 0

        return iter(effect)

    def _start_background_preload(self) -> None:
        """Start pre-loading next effect in background thread."""
        self._preload_ready.clear()
        thread = threading.Thread(target=self._preload_worker, daemon=True)
        thread.start()

    def _preload_worker(self) -> None:
        """Background worker to create next effect."""
        if len(self.enabled_effects) > 1:
            choices = [i for i in range(len(self.enabled_effects)) if i != self._current_index]
            next_idx = random.choice(choices)
        else:
            next_idx = 0

        # Create the effect (this is the slow part)
        next_iter = self._create_effect_iterator(next_idx)

        # Store results thread-safely
        with self._preload_lock:
            self._next_index = next_idx
            self._next_iterator = next_iter
        self._preload_ready.set()

    def get_current_effect_name(self) -> str:
        """Get the name of the currently active effect."""
        return self.enabled_effects[self._current_index]

    def switch_to_next_effect(self) -> None:
        """Switch to the pre-loaded next effect (instant, no stutter)."""
        # Wait for pre-load if not ready (should be ready by now)
        self._preload_ready.wait(timeout=0.1)

        with self._preload_lock:
            if self._next_iterator is not None:
                self._current_index = self._next_index
                self._current_iterator = self._next_iterator
                self._next_iterator = None
            self._effect_completed = False

        # Start background pre-load of the NEXT next effect
        self._start_background_preload()

    def get_next_frame(self) -> Optional[str]:
        """Get the next frame. Returns None when effect completes."""
        if self._current_iterator is None:
            return None

        try:
            return next(self._current_iterator)
        except StopIteration:
            self._effect_completed = True
            return None
