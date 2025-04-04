@echo off
cd /d %~dp0

if not exist ".git" (
    echo =============================
    echo To nie jest katalog repozytorium Git!
    echo Umiesc ten skrypt w folderze z projektem.
    pause
    exit /b
)

echo =============================
echo Pobieranie zmian z GitHub...
git pull

echo =============================
echo Gotowe. Wcisnij dowolny klawisz, aby zamknac.
pause
