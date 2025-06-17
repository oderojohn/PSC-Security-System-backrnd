@echo off
cd /d "C:\app\python Backend\myproject"

echo Starting Waitress server at %date% %time% >> "%USERPROFILE%\Desktop\waitress_log.txt"

"C:\Users\IT.Trainee\AppData\Local\Programs\Python\Python313\Scripts\waitress-serve.exe" --listen=0.0.0.0:8000 myproject.wsgi:application >> "%USERPROFILE%\Desktop\waitress_log.txt" 2>&1

pause
