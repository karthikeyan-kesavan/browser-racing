@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting the game server...
echo.
echo Open your browser and go to: http://localhost:5000
echo.
REM LINT:IGNORE W001
python server.py
