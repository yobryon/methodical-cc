@echo off
setlocal enabledelayedexpansion
REM cc - Resume a Claude Code session by persona name
REM
REM Usage:
REM   cc arch          Resume the session registered as "arch"
REM   cc impl          Resume the session registered as "impl"
REM   cc list          Show all registered sessions
REM   cc               Show usage
REM
REM Looks for a sessions file in .mam*/, .mama*/, or .pdt*/ state directories
REM in the current working directory. Sessions are registered via:
REM   /mam:session set <name>
REM   /mama:session set <name>

if "%~1"=="" goto :usage
if "%~1"=="help" goto :usage
if "%~1"=="-h" goto :usage
if "%~1"=="--help" goto :usage
if "%~1"=="list" goto :list

REM Lookup mode
set "FOUND_ID="
for %%D in (.mam .mama .pdt) do (
    if exist "%%D\sessions" (
        for /f "usebackq tokens=1,* delims==" %%A in ("%%D\sessions") do (
            if "%%A"=="%~1" set "FOUND_ID=%%B"
        )
    )
)
for /d %%D in (.mam-* .mama-* .pdt-*) do (
    if exist "%%D\sessions" (
        for /f "usebackq tokens=1,* delims==" %%A in ("%%D\sessions") do (
            if "%%A"=="%~1" set "FOUND_ID=%%B"
        )
    )
)

if not defined FOUND_ID (
    echo No session registered as '%~1'.
    echo.
    goto :list
)

claude -r %FOUND_ID%
goto :eof

:list
set "FOUND_ANY=0"
for %%D in (.mam .mama .pdt) do (
    if exist "%%D\sessions" (
        echo %%D\sessions:
        for /f "usebackq tokens=1,* delims==" %%A in ("%%D\sessions") do (
            echo   %%A  -^>  claude -r %%B
        )
        set "FOUND_ANY=1"
    )
)
for /d %%D in (.mam-* .mama-* .pdt-*) do (
    if exist "%%D\sessions" (
        echo %%D\sessions:
        for /f "usebackq tokens=1,* delims==" %%A in ("%%D\sessions") do (
            echo   %%A  -^>  claude -r %%B
        )
        set "FOUND_ANY=1"
    )
)
if "!FOUND_ANY!"=="0" (
    echo No sessions registered. Use /mam:session set ^<name^> or /mama:session set ^<name^> to register.
)
goto :eof

:usage
echo Usage: cc ^<name^>    Resume session registered as ^<name^>
echo        cc list      Show all registered sessions
echo.
echo Register sessions from inside Claude Code:
echo   /mam:session set arch
echo   /mama:session set arch
goto :eof
