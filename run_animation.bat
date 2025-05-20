@echo off
echo Creating spectacular RFM animation...
echo.

REM Make script executable first time
if not exist "%~dp0animate_rfm.py" (
  echo Error: animate_rfm.py file not found!
  exit /b 1
)

REM Ensure Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
  echo Error: Python is not installed or not in PATH!
  echo Please install Python from https://www.python.org/downloads/
  exit /b 1
)

REM Install required packages if running for the first time
if not exist "%~dp0packages_installed.txt" (
  echo Installing required packages...
  python -m pip install matplotlib numpy networkx pyyaml scipy pillow
  echo > "%~dp0packages_installed.txt"
)

REM Run animation script
echo.
echo Creating animation...
python animate_rfm.py --output rfm_animation --format gif --dpi 150 --fps 30 --duration 8

echo.
echo Animation complete! The output is saved as rfm_animation.gif
echo.
echo Press any key to open the animation...
pause > nul

REM Open the animation in the default program
start "" "rfm_animation.gif"

echo.
echo Press any key to exit...
pause > nul