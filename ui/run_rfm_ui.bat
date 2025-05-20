@echo off
:: RFM Architecture UI Launcher
:: This script launches the RFM Architecture UI application

echo Starting RFM Architecture UI...

:: Create logs directory if it doesn't exist
if not exist logs (
    mkdir logs
)

:: Create fonts directory if it doesn't exist
if not exist fonts (
    mkdir fonts
)

:: Check if Roboto fonts exist
if not exist fonts\Roboto-Regular.ttf (
    echo Downloading Roboto fonts...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf' -OutFile 'fonts\Roboto-Regular.ttf'"
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf' -OutFile 'fonts\Roboto-Bold.ttf'"
)

:: Activate virtual environment if it exists
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

:: Run the application
python -m rfm_ui.main %*

:: Check for errors
if %ERRORLEVEL% NEQ 0 (
    echo Error running RFM Architecture UI
    echo See logs for details
    pause
) else (
    echo RFM Architecture UI closed successfully
)

:: Deactivate virtual environment
if defined VIRTUAL_ENV (
    call deactivate
)