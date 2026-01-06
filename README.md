# TTE Screensaver

A Windows screensaver that displays ASCII art with animated terminal text effects using [TerminalTextEffects](https://github.com/ChrisBuilds/terminaltexteffects).

## Features

- Cycles through multiple TTE effects (Matrix, Rain, Decrypt, Beams, Burn, VHSTape, etc.)
- Customizable ASCII art - paste your own logos
- Configurable effect duration, font size, and FPS
- Standard Windows screensaver integration (/s, /c, /p flags)

## Requirements

- Windows 10/11
- Python 3.10+
- Dependencies: terminaltexteffects, pygame, pyinstaller

## Installation

### From Source (Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Run configuration dialog
python run.py

# Run screensaver (windowed for testing)
python run.py /s
```

### Build Windows Screensaver

```batch
# Run the build script
build.bat

# This creates dist/tte-screensaver.scr
```

### Install as Windows Screensaver

1. Copy `dist/tte-screensaver.scr` to `C:\Windows\System32\`
2. Right-click desktop → **Personalize** → **Lock screen** → **Screen saver settings**
3. Select **tte-screensaver** from the dropdown
4. Click **Settings** to configure ASCII art and effects

Or simply right-click the `.scr` file and select **Install**.

## Configuration

The configuration dialog allows you to:

- **ASCII Art**: Paste your custom ASCII art (generate at [patorjk.com/software/taag](https://patorjk.com/software/taag))
- **Effects**: Choose which effects to cycle through
- **Duration**: How long each effect runs before switching
- **Font Size**: Text rendering size
- **FPS**: Animation frame rate

Settings are stored in `%APPDATA%\tte-screensaver\config.json`

## Available Effects

35+ effects including:
- Matrix, Rain, Decrypt, Beams, Burn
- VHSTape, Slide, Spotlights, Spray, Swarm
- Blackhole, BouncyBalls, Bubbles, ColorShift
- Crumble, Expand, Fireworks, and many more

## Command Line Arguments

- `/s` - Run screensaver fullscreen
- `/c` - Show configuration dialog
- `/p <hwnd>` - Preview mode (not implemented)
- No args - Show configuration dialog

## Project Structure

```
tte-screensaver/
├── src/
│   ├── main.py           # Entry point
│   ├── screensaver.py    # Pygame main loop
│   ├── renderer.py       # ANSI → pygame rendering
│   ├── effects.py        # Effect management
│   ├── config.py         # Settings management
│   └── config_dialog.py  # Tkinter config UI
├── assets/
│   └── default_ascii.txt
├── requirements.txt
├── pyproject.toml
├── build.bat
└── run.py               # Development runner
```

## License

MIT
