
@echo off
cd /d %~dp0

:: Sprawdzenie czy to katalog repozytorium Git
if not exist ".git" (
    echo =============================
    echo To nie jest katalog repozytorium Git!
    pause
    exit /b
)

:: Próba powrotu na master lub main
git checkout master >nul 2>&1 || git checkout main >nul 2>&1

:: Wykryj nazwę głównej gałęzi (main lub master)
for /f "delims=" %%B in ('git symbolic-ref refs/remotes/origin/HEAD') do set "branch=%%~nxB"

echo =============================
set /p log_date=Podaj date od ktorej chcesz zobaczyc commity (np. 2025-04-04): 

:: Pobierz historię ze zdalnego repozytorium
echo.
echo Pobieranie najnowszej historii z GitHub...
git fetch origin

:: Pobierz listę commitów z podanej daty (czas lokalny +0200)
for /f "delims=" %%C in ('git log origin/%branch% --since="%log_date% 00:00:00 +0200" --oneline --reverse') do (
    set "has_commits=true"
    echo %%C
)

:: Jeśli nie znaleziono commitów
if not defined has_commits (
    echo -----------------------------
    echo Brak commitow od tej daty.
    pause
    exit /b
)

:: Zapytaj o commit
echo.
set /p commit_id=Skopiuj i wklej ID commita, do ktorego chcesz cofnac (np. e3a1f2c): 

:: Cofnij się do wybranego commita
echo.
git checkout %commit_id%

echo =============================
echo Cofnieto do commita %commit_id%
pause
