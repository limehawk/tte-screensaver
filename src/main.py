"""
TTE Screensaver - Main entry point.

Windows screensaver command-line arguments:
  /s - Run the screensaver in fullscreen mode
  /c - Show the configuration dialog
  /p <hwnd> - Preview mode (not implemented, just exits)
  (no args) - Show configuration dialog
"""

import sys


def main() -> None:
    """Main entry point for the screensaver."""
    args = [arg.lower() for arg in sys.argv[1:]]

    if not args:
        # No arguments - show config dialog
        from .config_dialog import show_config_dialog
        show_config_dialog()

    elif "/s" in args or "-s" in args:
        # Run screensaver in fullscreen
        from .screensaver import run_screensaver
        run_screensaver(fullscreen=True)

    elif "/c" in args or "-c" in args:
        # Show configuration dialog
        from .config_dialog import show_config_dialog
        show_config_dialog()

    elif "/p" in args or "-p" in args:
        # Preview mode - not implemented, just exit
        # Windows passes a window handle for preview, but we skip this
        sys.exit(0)

    else:
        # Unknown argument - show config dialog
        from .config_dialog import show_config_dialog
        show_config_dialog()


if __name__ == "__main__":
    main()
