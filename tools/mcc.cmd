@echo off
REM mcc - methodical-cc helper CLI (Windows shim)
REM
REM Locates Python and execs mcc.py with all arguments. The real implementation
REM lives in mcc.py — this shim exists for ergonomics and platform parity.

setlocal
set "SCRIPT_DIR=%~dp0"
set "PYTHON_SCRIPT=%SCRIPT_DIR%mcc.py"

if not exist "%PYTHON_SCRIPT%" (
    echo mcc: cannot find mcc.py at %PYTHON_SCRIPT% 1>&2
    exit /b 1
)

where python >nul 2>nul
if not errorlevel 1 (
    python "%PYTHON_SCRIPT%" %*
    exit /b %errorlevel%
)

where python3 >nul 2>nul
if not errorlevel 1 (
    python3 "%PYTHON_SCRIPT%" %*
    exit /b %errorlevel%
)

echo mcc: Python 3 is required but was not found on PATH. 1>&2
echo      Install Python 3.6+ from https://www.python.org/ 1>&2
exit /b 1
