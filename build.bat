@echo off
echo ========================================
echo  Building RobloxPianoPlayer.exe
echo ========================================
echo.

pip install pyinstaller --quiet

pyinstaller --onefile --windowed ^
    --name RobloxPianoPlayer ^
    --add-data "library;library" ^
    --hidden-import customtkinter ^
    --hidden-import mido.backends.rtmidi ^
    --collect-all supabase ^
    --splash splash.png ^
    main.py

echo.
echo Build complete! Check the dist/ folder.
pause
