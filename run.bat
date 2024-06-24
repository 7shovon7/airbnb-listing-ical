@echo off
REM Ensure the script is run from the directory where it is located
cd /d "%~dp0"

REM Navigate to the app_files directory
cd app_files

REM Activate virtual environment if it exists
if exist venv\Scripts\activate (
    call venv\Scripts\activate
) else (
    REM Create a virtual environment if it does not exist
    python -m venv venv
    call venv\Scripts\activate
    REM Install required packages
    pip install -r requirements.txt
)

REM Run the Flet application
flet run
