@echo off
cd /d "C:\Users\sabin\Desktop\placement_system"
call venv\Scripts\activate.bat
echo Training ML Model...
python model\train_model.py
pause
