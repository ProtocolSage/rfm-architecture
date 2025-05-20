@echo off
setlocal enabledelayedexpansion

:: RFM Architecture System Configuration Manager
:: Enhanced batch script with robust interpreter lookup and error handling

echo RFM Architecture System Configuration Manager
echo =============================================

:: Set up working directory to script location for reliable execution
pushd "%~dp0"

:: Try to find Python interpreter
set PYTHON_FOUND=0
set PYTHON_PATH=

:: Check for Python 3.7+ in PATH
for %%P in (python python3 py) do (
    where %%P >nul 2>nul
    if !errorlevel! equ 0 (
        for /f "tokens=*" %%V in ('%%P -c "import sys; print(sys.version_info[0]*10+sys.version_info[1])"') do (
            set PYTHON_VERSION=%%V
            if !PYTHON_VERSION! geq 37 (
                set PYTHON_PATH=%%P
                set PYTHON_FOUND=1
                echo Found Python !PYTHON_VERSION:~0,1!.!PYTHON_VERSION:~1,1! in PATH
                goto :FoundPython
            )
        )
    )
)

:: Check for Python in venv
if exist "venv\Scripts\python.exe" (
    set PYTHON_PATH=venv\Scripts\python.exe
    set PYTHON_FOUND=1
    echo Found Python in venv
    goto :FoundPython
)

:: Check for Python in .venv
if exist ".venv\Scripts\python.exe" (
    set PYTHON_PATH=.venv\Scripts\python.exe
    set PYTHON_FOUND=1
    echo Found Python in .venv
    goto :FoundPython
)

:: Check Windows Registry for Python installations
for /f "tokens=*" %%P in ('reg query HKEY_LOCAL_MACHINE\SOFTWARE\Python\PythonCore /f * /k 2^>nul ^| findstr /i "3\."') do (
    for /f "tokens=*" %%R in ('reg query "%%P\InstallPath" /ve 2^>nul ^| findstr "REG_SZ"') do (
        for /f "tokens=2*" %%A in ('echo %%R') do (
            if exist "%%B\python.exe" (
                set PYTHON_PATH="%%B\python.exe"
                set PYTHON_FOUND=1
                echo Found Python in registry: %%B
                goto :FoundPython
            )
        )
    )
)

:FoundPython
if %PYTHON_FOUND% equ 0 (
    echo Error: Python 3.7 or higher is required but not found.
    echo Please install Python from https://www.python.org/downloads/
    echo and make sure it's added to your PATH.
    goto :Error
)

:: Check for required dependencies
echo Checking dependencies...
%PYTHON_PATH% -c "import sys, dearpygui, yaml, numpy" >nul 2>nul
if errorlevel 1 (
    echo Missing dependencies. Attempting to install...
    %PYTHON_PATH% -m pip install -q dearpygui pyyaml numpy
    if errorlevel 1 (
        echo Error: Failed to install required dependencies.
        echo Please run: pip install dearpygui pyyaml numpy
        goto :Error
    )
)

:: Process command-line arguments
set ARGS=

:: Check for --help flag
if "%1"=="--help" goto :Help
if "%1"=="-h" goto :Help

:: Check for --version flag
if "%1"=="--version" goto :Version
if "%1"=="-v" goto :Version

:: Forward all arguments to the Python script
:ProcessArgs
if "%1"=="" goto :RunScript
set ARGS=%ARGS% %1
shift
goto :ProcessArgs

:RunScript
echo Starting System Configuration Manager...
%PYTHON_PATH% run_system_config.py%ARGS%

if errorlevel 1 (
    echo Error: System Configuration Manager exited with code %errorlevel%
    goto :Error
)

goto :End

:Help
echo Usage: run_system_config.bat [OPTIONS]
echo.
echo Options:
echo   --config PATH        Path to configuration file to open on startup
echo   --schema PATH        Path to configuration schema file for validation
echo   --log-level LEVEL    Set logging level (debug, info, warning, error, critical)
echo   --log-file PATH      Path to log file
echo   --width WIDTH        Set window width (default: 1280)
echo   --height HEIGHT      Set window height (default: 800)
echo   --version            Show version information and exit
echo   --help               Show this help message and exit
goto :End

:Version
echo RFM Architecture System Configuration Manager v1.0
goto :End

:Error
echo.
echo Press any key to exit...
pause >nul
exit /b 1

:End
echo.
popd
exit /b 0