@echo off
chcp 65001 >nul
setlocal

echo ========================================================
echo VerbaMind - Nuitka Build (optimized)
echo ========================================================

REM === Configuration ===
set MAIN_FILE=verbamind\main.py
set BACKEND_FILE=verbamind\backend\main.py

REM === Detect CPU cores ===
set CPU_CORES=%NUMBER_OF_PROCESSORS%
if not defined CPU_CORES set CPU_CORES=4
set /a BUILD_JOBS=%CPU_CORES%

REM === Module exclusion list ===
set EXCLUDE_MODULES=unittest,test,pytest,_pytest,doctest,pdb,pdbpp
set EXCLUDE_MODULES=%EXCLUDE_MODULES%,setuptools,pip,distutils,pkg_resources
set EXCLUDE_MODULES=%EXCLUDE_MODULES%,email.mime,http.server,xmlrpc

REM Nuitka names the output folder after the main script (main.dist).
REM Both builds use "main.py", so we rename after each build.

if exist dist\main.dist rmdir /s /q dist\main.dist

echo.
echo ========================================================
echo [1] GUI - VerbaMind.exe
echo ========================================================
if exist "dist\VerbaMind.dist\VerbaMind.exe" (
    echo [SKIP] already built.
    goto gui_done
)

python -m nuitka --standalone --windows-console-mode=disable --jobs=%BUILD_JOBS% ^
    --enable-plugin=anti-bloat --enable-plugin=pyside6 ^
    --noinclude-pytest-mode=nofollow --noinclude-setuptools-mode=nofollow ^
    --nofollow-import-to=%EXCLUDE_MODULES% --python-flag=no_docstrings ^
    --output-dir=dist --output-filename=VerbaMind.exe --remove-output %MAIN_FILE%
if errorlevel 1 goto error_gui

if exist dist\main.dist move dist\main.dist dist\VerbaMind.dist >nul
:gui_done

echo.
echo ========================================================
echo [2] Backend - backend.exe
echo ========================================================
if exist "dist\backend.dist\backend.exe" (
    echo [SKIP] already built.
    goto backend_done
)

python -m nuitka --standalone --windows-console-mode=force --jobs=4 ^
    --enable-plugin=anti-bloat ^
    --include-module=av.utils ^
    --include-package=langchain_core ^
    --include-package=faiss ^
    --include-module=langchain_community.vectorstores.faiss ^
    --include-module=langchain_community.docstore.in_memory ^
    --include-module=langchain_community.docstore.base ^
    --noinclude-pytest-mode=nofollow --noinclude-setuptools-mode=nofollow ^
    --noinclude-numba-mode=nofollow ^
    --nofollow-import-to=%EXCLUDE_MODULES% ^
    --output-dir=dist --output-filename=backend.exe --remove-output %BACKEND_FILE%
if errorlevel 1 goto error_backend

if exist dist\main.dist move dist\main.dist dist\backend.dist >nul
:backend_done

echo.
echo [3] Slimming dist folders...
powershell -ExecutionPolicy Bypass -File installer\slim_dist.ps1 -DistPath "dist"

echo.
echo ========================================================
echo Build complete!
echo   dist\VerbaMind.dist\VerbaMind.exe  (GUI)
echo   dist\backend.dist\backend.exe       (Backend)
echo Next: compile installer\verbamind.iss with Inno Setup
echo ========================================================
goto :eof

:error_gui
echo [ERROR] GUI build failed!
pause
exit /b 1

:error_backend
echo [ERROR] Backend build failed!
pause
exit /b 1
