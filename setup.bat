@echo off
title Python Environment Setup
echo ===============================
echo   Python + Git + Packages Setup
echo ===============================

:: -------------------------------
:: Check Python
:: -------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Installing Python...
    winget install -e --id Python.Python.3
) else (
    echo Python already installed.
)

:: ===============================
:: REQUIRED PACKAGES
:: =============================== 
echo.
echo Installing REQUIRED packages...

python -m pip install ^
requests ^
pywin32 ^
winshell ^
psutil ^
pyautogui ^
pyperclip ^
|| python3 -m pip install ^
requests ^
pywin32 ^
winshell ^
psutil ^
pyautogui ^
pyperclip

:: ===============================
:: OPTIONAL PACKAGES
:: ===============================
echo.
echo Installing OPTIONAL packages...

for %%P in (
    pyarmor
    pyinstaller
    nuitka
    comtypes
) do (
    echo Installing %%P...
    python -m pip install %%P || python3 -m pip install %%P
)

echo.
echo ===============================
echo   Setup Completed Successfully
echo ===============================
pause
