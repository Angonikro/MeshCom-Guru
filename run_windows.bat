@echo off
setlocal
cd /d "%~dp0"

echo.
echo ========================================
echo   MeshCom-Guru v0.3.60 - Windows
echo ========================================
echo.

python -c "import sys; print('Python:', sys.version)"
if errorlevel 1 (
    echo.
    echo FEHLER: Python wurde nicht gefunden.
    echo Bitte Python 3.10 bis 3.14 installieren und "Add Python to PATH" aktivieren.
    pause
    exit /b 1
)

python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) and sys.version_info < (3,15) else 1)"
if errorlevel 1 (
    echo.
    echo FEHLER: Diese MeshCom-Guru-Version benoetigt Python 3.10 bis 3.14.
    echo Die aktuell verwendete Python-Version ist nicht kompatibel.
    pause
    exit /b 1
)

echo.
echo Installiere benoetigte Python-Pakete ...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo FEHLER: Die benoetigten Pakete konnten nicht installiert werden.
    echo.
    echo Hinweis: PySide6 WebEngine wird ueber PySide6-Addons[webengine] installiert.
    pause
    exit /b 1
)

echo.
echo Starte MeshCom-Guru ...
python main.py
set EXITCODE=%ERRORLEVEL%

if not "%EXITCODE%"=="0" (
    echo.
    echo MeshCom-Guru wurde mit Fehlercode %EXITCODE% beendet.
)

pause
exit /b %EXITCODE%
