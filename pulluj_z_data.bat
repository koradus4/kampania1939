@echo off
cd /d %~dp0

if not exist ".git" (
    echo =============================
    echo To nie jest katalog repozytorium Git!
    pause
    exit /b
)

echo =============================
set /p log_date=Podaj date od ktorej chcesz zobaczyc commity (np. 2025-04-01): 

echo.
echo ==== Commity od %log_date% ====
git log --since="%log_date%" --oneline --reverse
echo =============================

set /p commit_id=Skopiuj i wklej ID commita, do ktorego chcesz cofnac (np. e3a1f2c): 

echo.
git checkout %commit_id%

echo =============================
echo Cofnieto do commita %commit_id%
pause
