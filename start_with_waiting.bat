@echo off
echo Redémarrage de GLPIbis...
echo.
echo Ouvrez votre navigateur sur: http://127.0.0.1:5000/waiting
echo.
echo Appuyez sur une touche pour démarrer l'application...
pause > nul

cd /d "c:\Users\opm85\OneDrive\Documents\GitHub\GLPIbis"
python app.py

pause