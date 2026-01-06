"""Configuration dialog using tkinter."""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import List

from .config import Config, load_config, save_config
from .effects import get_available_effect_names


class ConfigDialog:
    """Configuration dialog for the screensaver."""

    def __init__(self):
        self.config = load_config()
        self.root = tk.Tk()
        self.root.title("TTE Screensaver Settings")
        self.root.geometry("800x700")
        self.root.resizable(True, True)

        # Store checkbox variables
        self.effect_vars: dict[str, tk.BooleanVar] = {}

        self._create_widgets()
        self._load_current_config()

    def _create_widgets(self) -> None:
        """Create the dialog widgets."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ASCII Art section
        art_label = ttk.Label(main_frame, text="ASCII Art:", font=("", 10, "bold"))
        art_label.pack(anchor=tk.W, pady=(0, 5))

        art_hint = ttk.Label(
            main_frame,
            text="Paste your ASCII art below. Generate at: patorjk.com/software/taag",
            font=("", 8),
        )
        art_hint.pack(anchor=tk.W)

        # ASCII art text area with monospace font
        self.art_text = scrolledtext.ScrolledText(
            main_frame,
            width=80,
            height=15,
            font=("Consolas", 10),
            wrap=tk.NONE,
        )
        self.art_text.pack(fill=tk.BOTH, expand=True, pady=(5, 10))

        # Add horizontal scrollbar
        h_scroll = ttk.Scrollbar(
            self.art_text, orient=tk.HORIZONTAL, command=self.art_text.xview
        )
        self.art_text.configure(xscrollcommand=h_scroll.set)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        # Effects section
        effects_label = ttk.Label(
            main_frame, text="Enabled Effects:", font=("", 10, "bold")
        )
        effects_label.pack(anchor=tk.W, pady=(10, 5))

        # Effects frame with scrollable canvas
        effects_container = ttk.Frame(main_frame)
        effects_container.pack(fill=tk.X, pady=(0, 10))

        # Create a canvas with scrollbar for effects
        effects_canvas = tk.Canvas(effects_container, height=120)
        effects_scrollbar = ttk.Scrollbar(
            effects_container, orient=tk.VERTICAL, command=effects_canvas.yview
        )
        effects_frame = ttk.Frame(effects_canvas)

        effects_frame.bind(
            "<Configure>",
            lambda e: effects_canvas.configure(scrollregion=effects_canvas.bbox("all")),
        )

        effects_canvas.create_window((0, 0), window=effects_frame, anchor=tk.NW)
        effects_canvas.configure(yscrollcommand=effects_scrollbar.set)

        effects_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        effects_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create checkboxes for each effect (in columns)
        available_effects = get_available_effect_names()
        num_cols = 4
        for idx, effect_name in enumerate(available_effects):
            var = tk.BooleanVar(value=effect_name in self.config.enabled_effects)
            self.effect_vars[effect_name] = var

            row = idx // num_cols
            col = idx % num_cols

            cb = ttk.Checkbutton(effects_frame, text=effect_name, variable=var)
            cb.grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)

        # Settings section
        settings_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        # Font size
        font_frame = ttk.Frame(settings_frame)
        font_frame.pack(fill=tk.X, pady=2)

        ttk.Label(font_frame, text="Font Size:").pack(side=tk.LEFT)
        self.font_var = tk.StringVar(value=str(self.config.font_size))
        font_entry = ttk.Entry(font_frame, textvariable=self.font_var, width=10)
        font_entry.pack(side=tk.LEFT, padx=(10, 0))

        # FPS
        fps_frame = ttk.Frame(settings_frame)
        fps_frame.pack(fill=tk.X, pady=2)

        ttk.Label(fps_frame, text="Target FPS:").pack(side=tk.LEFT)
        self.fps_var = tk.StringVar(value=str(self.config.target_fps))
        fps_entry = ttk.Entry(fps_frame, textvariable=self.fps_var, width=10)
        fps_entry.pack(side=tk.LEFT, padx=(10, 0))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="Save", command=self._save).pack(
            side=tk.RIGHT, padx=(5, 0)
        )
        ttk.Button(button_frame, text="Cancel", command=self._cancel).pack(
            side=tk.RIGHT
        )
        ttk.Button(button_frame, text="Preview", command=self._preview).pack(
            side=tk.LEFT
        )

    def _load_current_config(self) -> None:
        """Load current config values into the dialog."""
        # Set ASCII art
        self.art_text.delete("1.0", tk.END)
        self.art_text.insert("1.0", self.config.ascii_art)

        # Effect checkboxes are already set in _create_widgets

    def _get_enabled_effects(self) -> List[str]:
        """Get list of enabled effects from checkboxes."""
        return [name for name, var in self.effect_vars.items() if var.get()]

    def _validate_and_get_config(self) -> Config | None:
        """Validate inputs and return new config, or None if invalid."""
        try:
            font_size = int(self.font_var.get())
            if font_size <= 0:
                raise ValueError("Font size must be positive")
        except ValueError:
            messagebox.showerror("Error", "Invalid font size. Must be a positive integer.")
            return None

        try:
            fps = int(self.fps_var.get())
            if fps <= 0:
                raise ValueError("FPS must be positive")
        except ValueError:
            messagebox.showerror("Error", "Invalid FPS. Must be a positive integer.")
            return None

        enabled_effects = self._get_enabled_effects()
        if not enabled_effects:
            messagebox.showerror("Error", "Please select at least one effect.")
            return None

        ascii_art = self.art_text.get("1.0", tk.END).rstrip()
        if not ascii_art.strip():
            messagebox.showerror("Error", "Please enter some ASCII art.")
            return None

        return Config(
            ascii_art=ascii_art,
            enabled_effects=enabled_effects,
            font_size=font_size,
            background_color=self.config.background_color,
            target_fps=fps,
        )

    def _save(self) -> None:
        """Save configuration and close dialog."""
        new_config = self._validate_and_get_config()
        if new_config:
            save_config(new_config)
            messagebox.showinfo("Success", "Settings saved successfully!")
            self.root.destroy()

    def _cancel(self) -> None:
        """Close dialog without saving."""
        self.root.destroy()

    def _preview(self) -> None:
        """Run a preview of the screensaver with current settings."""
        new_config = self._validate_and_get_config()
        if new_config:
            # Import here to avoid circular imports
            from .screensaver import run_screensaver

            # Hide the dialog while previewing
            self.root.withdraw()
            try:
                run_screensaver(fullscreen=False, config=new_config)
            finally:
                self.root.deiconify()

    def run(self) -> None:
        """Run the dialog."""
        self.root.mainloop()


def show_config_dialog() -> None:
    """Show the configuration dialog."""
    dialog = ConfigDialog()
    dialog.run()
