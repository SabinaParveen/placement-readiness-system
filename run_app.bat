@echo off
cd /d "C:\Users\sabin\Desktop\placement_system"
call venv\Scripts\activate.bat
echo.
echo  Starting PlaceReady AI...
echo  Open browser at: http://localhost:5000
echo.
python app.py
pause
