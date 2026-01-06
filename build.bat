@echo off
REM Build script for TTE Screensaver
REM Creates a .scr file that can be installed as a Windows screensaver

echo Building TTE Screensaver...

REM Install dependencies if needed
pip install -r requirements.txt

REM Build with PyInstaller
pyinstaller --onefile --windowed ^
    --name "tte-screensaver" ^
    --add-data "assets;assets" ^
    --hidden-import terminaltexteffects.effects.effect_beams ^
    --hidden-import terminaltexteffects.effects.effect_binarypath ^
    --hidden-import terminaltexteffects.effects.effect_blackhole ^
    --hidden-import terminaltexteffects.effects.effect_bouncyballs ^
    --hidden-import terminaltexteffects.effects.effect_bubbles ^
    --hidden-import terminaltexteffects.effects.effect_burn ^
    --hidden-import terminaltexteffects.effects.effect_colorshift ^
    --hidden-import terminaltexteffects.effects.effect_crumble ^
    --hidden-import terminaltexteffects.effects.effect_decrypt ^
    --hidden-import terminaltexteffects.effects.effect_errorcorrect ^
    --hidden-import terminaltexteffects.effects.effect_expand ^
    --hidden-import terminaltexteffects.effects.effect_fireworks ^
    --hidden-import terminaltexteffects.effects.effect_highlight ^
    --hidden-import terminaltexteffects.effects.effect_laseretch ^
    --hidden-import terminaltexteffects.effects.effect_matrix ^
    --hidden-import terminaltexteffects.effects.effect_middleout ^
    --hidden-import terminaltexteffects.effects.effect_orbittingvolley ^
    --hidden-import terminaltexteffects.effects.effect_overflow ^
    --hidden-import terminaltexteffects.effects.effect_pour ^
    --hidden-import terminaltexteffects.effects.effect_print ^
    --hidden-import terminaltexteffects.effects.effect_rain ^
    --hidden-import terminaltexteffects.effects.effect_random_sequence ^
    --hidden-import terminaltexteffects.effects.effect_rings ^
    --hidden-import terminaltexteffects.effects.effect_scattered ^
    --hidden-import terminaltexteffects.effects.effect_slice ^
    --hidden-import terminaltexteffects.effects.effect_slide ^
    --hidden-import terminaltexteffects.effects.effect_spotlights ^
    --hidden-import terminaltexteffects.effects.effect_spray ^
    --hidden-import terminaltexteffects.effects.effect_swarm ^
    --hidden-import terminaltexteffects.effects.effect_sweep ^
    --hidden-import terminaltexteffects.effects.effect_synthgrid ^
    --hidden-import terminaltexteffects.effects.effect_unstable ^
    --hidden-import terminaltexteffects.effects.effect_vhstape ^
    --hidden-import terminaltexteffects.effects.effect_waves ^
    --hidden-import terminaltexteffects.effects.effect_wipe ^
    run.py

REM Rename to .scr
if exist "dist\tte-screensaver.exe" (
    copy "dist\tte-screensaver.exe" "dist\tte-screensaver.scr"
    echo.
    echo Build complete!
    echo.
    echo To install the screensaver:
    echo   1. Copy dist\tte-screensaver.scr to C:\Windows\System32\
    echo   2. Right-click desktop ^> Personalize ^> Lock screen ^> Screen saver settings
    echo   3. Select "tte-screensaver" from the dropdown
    echo.
    echo Or just right-click the .scr file and select "Install"
) else (
    echo Build failed!
    exit /b 1
)
