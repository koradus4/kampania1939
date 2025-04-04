@echo off
echo Uruchamianie Kampania Wrzesniowa 1939...
python main.py
if errorlevel 1 (
    echo Wystapil problem podczas uruchamiania gry.
    echo Sprobuj alternatywna metode:
    echo python3 main.py
    pause
)
