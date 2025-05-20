@echo off
:: RFM Architecture Configuration Validator
:: This script validates the configuration file for RFM Architecture
::
:: Usage:
::   validate_config.bat [config_file]
::
:: If no config_file is provided, it defaults to 'config.yaml'.

echo RFM Architecture Configuration Validator

set CONFIG_FILE=%1
if "%CONFIG_FILE%"=="" set CONFIG_FILE=config.yaml

python validate_config.py %CONFIG_FILE%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Configuration validation successful!
) else (
    echo.
    echo Configuration validation failed. Please fix the errors and try again.
)

pause