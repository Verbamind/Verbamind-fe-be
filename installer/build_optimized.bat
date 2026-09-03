@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================================
echo VerbaMind — Nuitka Build (optimized)
echo ========================================================

REM === Configuration ===
set APP_NAME=VerbaMind
set MAIN_FILE=verbamind\main.py
set BACKEND_FILE=verbamind\backend\main.py
set VERSION=0.1.0

REM === Detect CPU cores ===
set CPU_CORES=%NUMBER_OF_PROCESSORS%
if not defined CPU_CORES set CPU_CORES=4
set /a BUILD_JOBS=%CPU_CORES%

REM === Module exclusion list ===
set EXCLUDE_MODULES=unittest,test,pytest,_pytest,doctest,pdb,pdbpp
set EXCLUDE_MODULES=%EXCLUDE_MODULES%,setuptools,pip,distutils,pkg_resources
set EXCLUDE_MODULES=%EXCLUDE_MODULES%,email.mime,http.server,xmlrpc,pydoc

REM Nuitka names the output folder after the main script (main.dist).
REM Both builds use "main.py", so we rename after each build to keep
REM dist\VerbaMind.dist and dist\backend.dist separate.

echo.
echo [1/5] Cleaning stale main.dist...
if exist dist\main.dist rmdir /s /q dist\main.dist

echo.
echo [2/5] Building GUI (VerbaMind.exe)...
echo   CPU cores: %BUILD_JOBS%
echo.

if exist "dist\VerbaMind.dist\VerbaMind.exe" (
    echo [SKIP] GUI already built: dist\VerbaMind.dist\VerbaMind.exe
) else (
python -m nuitka ^
    --standalone ^
    --windows-console-mode=disable ^
    --jobs=%BUILD_JOBS% ^
    --enable-plugin=anti-bloat ^
    --enable-plugin=pyside6 ^
    --noinclude-pytest-mode=nofollow ^
    --noinclude-setuptools-mode=nofollow ^
    --nofollow-import-to=%EXCLUDE_MODULES% ^
    --python-flag=no_docstrings ^
    --output-dir=dist ^
    --output-filename=VerbaMind.exe ^
    --remove-output ^
    %MAIN_FILE%

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] GUI build failed!
    pause
    exit /b 1
)

REM Separate GUI output folder
if exist dist\main.dist (
    move dist\main.dist dist\VerbaMind.dist >nul
    echo [OK] GUI -> dist\VerbaMind.dist
)
)

echo.
echo [3/5] Building Backend (backend.exe)...
echo.

if exist "dist\backend.dist\backend.exe" (
    echo [SKIP] Backend already built: dist\backend.dist\backend.exe
) else (
python -m nuitka ^
    --standalone ^
    --windows-console-mode=force ^
    --jobs=4 ^
    --enable-plugin=anti-bloat ^
    --noinclude-pytest-mode=nofollow ^
    --noinclude-setuptools-mode=nofollow ^
    --noinclude-numba-mode=nofollow ^
    --nofollow-import-to=%EXCLUDE_MODULES% ^
    --python-flag=no_docstrings ^
    --output-dir=dist ^
    --output-filename=backend.exe ^
    --remove-output ^
    %BACKEND_FILE%

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Backend build failed!
    pause
    exit /b 1
)

REM Separate backend output folder
if exist dist\main.dist (
    move dist\main.dist dist\backend.dist >nul
    echo [OK] Backend -> dist\backend.dist
)
)

echo.
echo [4/5] Slimming dist folders...
powershell -ExecutionPolicy Bypass -File installer\slim_dist.ps1 -DistPath "dist"

echo.
echo [5/5] Build complete!
echo.
echo   dist\VerbaMind.dist\VerbaMind.exe  (GUI)
echo   dist\backend.dist\backend.exe       (Backend service)
echo.
echo Next: Run Inno Setup compiler on installer\verbamind.iss
echo ========================================================
pause
