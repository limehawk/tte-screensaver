# TTE Screensaver for Windows

**Bring the iconic Omarchy Linux screensaver experience to Windows.** Stunning terminal text effects animate your custom ASCII art across all your monitors.

[![Download](https://img.shields.io/github/v/release/limehawk/tte-screensaver?label=Download&style=for-the-badge)](https://github.com/limehawk/tte-screensaver/releases/latest)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

---

## What is this?

If you've seen [Omarchy Linux](https://github.com/basecamp/omarchy) and loved their mesmerizing terminal screensaver effects, you've probably wished you could have the same thing on Windows. **Now you can.**

TTE Screensaver brings 35+ animated terminal effects to Windows, rendering your custom ASCII art with the same visual flair that made Omarchy's screensaver famous.

### Features

- **Multi-Monitor Support** - Each monitor runs its own independent effect with centered ASCII art
- **35+ Visual Effects** - Matrix, Rain, Decrypt, Beams, Burn, Blackhole, VHSTape, and many more
- **Custom ASCII Art** - Display your company logo, name, or any ASCII art you want
- **Random Effect Cycling** - Effects run to completion then switch randomly
- **Native Windows Integration** - Installs as a proper Windows screensaver (.scr)
- **Configurable** - Adjust font size, FPS, and choose which effects to enable

---

## Quick Start

### Download & Install

1. Download `tte-screensaver.scr` from the [latest release](https://github.com/limehawk/tte-screensaver/releases/latest)
2. Right-click the `.scr` file → **Install**
3. Or copy to `C:\Windows\System32\` for system-wide install

### Configure

1. Right-click desktop → **Personalize** → **Lock screen** → **Screen saver settings**
2. Select **tte-screensaver** from the dropdown
3. Click **Settings** to customize your ASCII art and effects

---

## Configuration Options

| Setting | Description |
|---------|-------------|
| **ASCII Art** | Your custom text/logo (generate at [patorjk.com/software/taag](https://patorjk.com/software/taag)) |
| **Enabled Effects** | Select which of the 35+ effects to cycle through |
| **Font Size** | Text rendering size (default: 20) |
| **Target FPS** | Animation smoothness (default: 100) |

Settings stored in `%APPDATA%\tte-screensaver\config.json`

---

## Available Effects

<details>
<summary>Click to see all 35+ effects</summary>

- Beams, BinaryPath, Blackhole, BouncyBalls, Bubbles
- Burn, ColorShift, Crumble, Decrypt, ErrorCorrect
- Expand, Fireworks, Highlight, LaserEtch, Matrix
- MiddleOut, OrbittingVolley, Overflow, Pour, Print
- Rain, RandomSequence, Rings, Scattered, Slice
- Slide, Spotlights, Spray, Swarm, Sweep
- SynthGrid, Unstable, VHSTape, Waves, Wipe

</details>

---

## Building from Source

```bash
# Clone the repo
git clone https://github.com/limehawk/tte-screensaver.git
cd tte-screensaver

# Install dependencies
pip install -r requirements.txt

# Run in development mode
python run.py        # Config dialog
python run.py /s     # Screensaver (windowed)

# Build the .scr file
build.bat
# Output: dist/tte-screensaver.scr
```

### Requirements

- Windows 10/11
- Python 3.10+
- Dependencies: terminaltexteffects, pygame

---

## Command Line

| Flag | Action |
|------|--------|
| `/s` | Run screensaver fullscreen |
| `/c` | Show configuration dialog |
| `/p` | Preview mode (not implemented) |
| *(none)* | Show configuration dialog |

---

## Credits

- Powered by [TerminalTextEffects](https://github.com/ChrisBuilds/terminaltexteffects) by ChrisBuilds
- Inspired by [Omarchy Linux](https://github.com/basecamp/omarchy) screensaver

---

## Keywords

`windows screensaver` `terminal effects` `ascii art` `omarchy` `matrix effect` `terminal text effects` `tte` `animated screensaver` `multi-monitor screensaver` `custom screensaver`

---

## License

MIT License - see [LICENSE](LICENSE)
