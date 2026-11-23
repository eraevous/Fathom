@echo off
rem Fathom per-user installer for Windows (spec 031). Double-click to install or upgrade.
rem No admin rights needed. Pass --uninstall or --dry-run from a terminal if you want those.
setlocal
set "HERE=%~dp0"
py -3 -c "import sys; sys.exit(sys.version_info < (3, 11))" >nul 2>nul
if not errorlevel 1 goto use_py
python -c "import sys; sys.exit(sys.version_info < (3, 11))" >nul 2>nul
if not errorlevel 1 goto use_python
echo.
echo Fathom needs Python 3.11 or newer, and none was found.
echo Get the Windows installer from https://www.python.org/downloads/windows/
echo In the installer, leave "Use admin privileges when installing py.exe" unticked:
echo it then installs for you only and needs no admin rights. Then run this again.
goto done
:use_py
py -3 "%HERE%fathom_install.py" %*
goto done
:use_python
python "%HERE%fathom_install.py" %*
:done
echo.
pause
