@echo off
setlocal enabledelayedexpansion

:: Rename video files from P#######.MP4 to YYYYMMDD_HHMMSS.mp4
:: using video creation date/time from metadata
:: Requires ffprobe (part of ffmpeg) to be in PATH

echo.
echo Video File Renamer - P#######.MP4 to YYYYMMDD_HHMMSS.mp4
echo ========================================================
echo.

:: Check if ffprobe is available
where ffprobe >nul 2>&1
if errorlevel 1 (
    echo ERROR: ffprobe not found in PATH
    echo Please install ffmpeg from https://ffmpeg.org/download.html
    echo and add it to your system PATH
    echo.
    pause
    exit /b 1
)

:: Set target directory (use current directory if not specified)
if "%~1"=="" (
    set "TARGET_DIR=%CD%"
) else (
    set "TARGET_DIR=%~1"
)

echo Target directory: !TARGET_DIR!
echo.

:: Count files matching pattern
set /a COUNT=0
for %%F in ("!TARGET_DIR!\P*.MP4" "!TARGET_DIR!\P*.mp4") do (
    set "FILENAME=%%~nxF"
    echo !FILENAME! | findstr /r "^P[0-9][0-9][0-9][0-9][0-9][0-9][0-9]\.MP4$" >nul 2>&1
    if !errorlevel! equ 0 set /a COUNT+=1
)

if !COUNT! equ 0 (
    echo No files matching P#######.MP4 pattern found
    echo.
    pause
    exit /b 0
)

echo Found !COUNT! video file^(s^) to process
echo.

:: Check if dry run or execute mode
set "DRY_RUN=1"
if /i "%~2"=="--execute" set "DRY_RUN=0"
if /i "%~2"=="-x" set "DRY_RUN=0"

if !DRY_RUN! equ 1 (
    echo MODE: DRY RUN - No files will be renamed
) else (
    echo MODE: EXECUTE - Files WILL be renamed
    echo.
    set /p "CONFIRM=Are you sure you want to rename files? (Y/N): "
    if /i "!CONFIRM!" neq "Y" (
        echo Cancelled.
        exit /b 0
    )
)
echo.

:: Process each matching file
set /a RENAMED=0
set /a ERRORS=0

for %%F in ("!TARGET_DIR!\P*.MP4" "!TARGET_DIR!\P*.mp4") do (
    set "FILENAME=%%~nxF"
    set "FULLPATH=%%~fF"
    
    :: Check if filename matches pattern P#######.MP4
    echo !FILENAME! | findstr /r "^P[0-9][0-9][0-9][0-9][0-9][0-9][0-9]\.MP4$" >nul 2>&1
    if !errorlevel! equ 0 (
        :: Get creation time from video metadata using ffprobe
        for /f "delims=" %%T in ('ffprobe -v quiet -select_streams v:0 -show_entries stream_tags^=creation_time -of default^=noprint_wrappers^=1:nokey^=1 "!FULLPATH!" 2^>nul') do (
            set "CREATION_TIME=%%T"
        )
        
        :: If no creation time in stream, try format tags
        if "!CREATION_TIME!"=="" (
            for /f "delims=" %%T in ('ffprobe -v quiet -show_entries format_tags^=creation_time -of default^=noprint_wrappers^=1:nokey^=1 "!FULLPATH!" 2^>nul') do (
                set "CREATION_TIME=%%T"
            )
        )
        
        if "!CREATION_TIME!"=="" (
            :: Fallback to file modification time
            set "NEW_NAME="
            for %%A in ("!FULLPATH!") do (
                set "FILEDATE=%%~tA"
                :: Parse date/time from format: MM/DD/YYYY HH:MM AM/PM
                for /f "tokens=1-3 delims=/ " %%D in ("!FILEDATE!") do (
                    set "MM=%%D"
                    set "DD=%%E"
                    set "YYYY=%%F"
                )
                for /f "tokens=1-2 delims=: " %%H in ("!FILEDATE:*:=!") do (
                    set "HH=%%H"
                    set "MIN=%%I"
                )
                :: Pad with zeros if needed
                if "!MM:~1,1!"=="" set "MM=0!MM!"
                if "!DD:~1,1!"=="" set "DD=0!DD!"
                if "!HH:~1,1!"=="" set "HH=0!HH!"
                if "!MIN:~1,1!"=="" set "MIN=0!MIN!"
                set "NEW_NAME=!YYYY!!MM!!DD!_!HH!!MIN!00.mp4"
            )
            echo   !FILENAME! -^> !NEW_NAME! [using file time]
        ) else (
            :: Parse ISO datetime: 2024-01-15T14:30:45.000000Z
            set "DATETIME=!CREATION_TIME:~0,19!"
            set "DATETIME=!DATETIME:T=!"
            set "DATETIME=!DATETIME::=!"
            set "DATETIME=!DATETIME:-=!"
            set "NEW_NAME=!DATETIME:~0,8!_!DATETIME:~8,6!.mp4"
            echo   !FILENAME! -^> !NEW_NAME!
        )
        
        :: Check if target exists
        if exist "!TARGET_DIR!\!NEW_NAME!" (
            echo     [SKIPPED: target exists]
            set /a ERRORS+=1
        ) else (
            if !DRY_RUN! equ 1 (
                echo     [would rename]
            ) else (
                ren "!FULLPATH!" "!NEW_NAME!" 2>nul
                if !errorlevel! equ 0 (
                    echo     [renamed]
                    set /a RENAMED+=1
                ) else (
                    echo     [ERROR: rename failed]
                    set /a ERRORS+=1
                )
            )
        )
    )
)

echo.
if !DRY_RUN! equ 1 (
    echo DRY RUN complete. !COUNT! file^(s^) would be processed.
    echo.
    echo To actually rename files, run with --execute or -x flag:
    echo   %~nx0 --execute
) else (
    echo Renamed !RENAMED! file^(s^). !ERRORS! error^(s^).
)
echo.
pause
