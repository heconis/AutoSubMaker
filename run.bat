@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_EXE=.venv\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
  echo Virtual environment was not found: %PYTHON_EXE%
  echo Create it first with:
  echo   python -m venv .venv
  echo   .venv\Scripts\activate
  echo   python -m pip install -e .[dev]
  pause
  exit /b 1
)

"%PYTHON_EXE%" -m autosubmaker
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
  echo.
  echo AutoSubMaker exited with code %EXIT_CODE%.
  pause
)

exit /b %EXIT_CODE%
