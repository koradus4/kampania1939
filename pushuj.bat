@echo off
cd /d %~dp0

if not exist ".git" (
    echo =============================
    echo To nie jest katalog repozytorium Git!
    echo Umiesc pushuj.bat w folderze z projektem.
    pause
    exit /b
)

echo =============================
echo Dodawanie wszystkich zmian...
git add .

set /p commit_msg=Podaj tresc commita: 
git commit -m "%commit_msg%"

echo =============================
echo Wysylanie na GitHub...
git push

echo =============================
echo Zrobione!
pause
