@echo off
REM ============================================================
REM  regenera.bat - Regenera episodis vells amb la veu Azure
REM  Us:  regenera.bat 1 2 3 4 5 6 7 8 9
REM  (llista de numeros d'episodi a regenerar)
REM ============================================================

REM --- MATEIXA CONFIGURACIO que podcast_pc.bat ---
set "GH_TOKEN=EL_TEU_TOKEN_DE_GITHUB"
set "AZURE_KEY=LA_TEVA_CLAU_AZURE"
set "AZURE_REGION=francecentral"
set "WORKDIR=%USERPROFILE%\podcast-gestio"
set "FFMPEG_DIR=C:\podcast"
REM -----------------------------------------------

set "AZURE_VOICE=ca-ES-JoanaNeural"
set "REPO_URL=https://x-access-token:%GH_TOKEN%@github.com/RamonRamon1973/podcast-llibres.git"

if "%~1"=="" (
    echo Us: regenera.bat 1 2 3 ...  ^(numeros d'episodi a regenerar^)
    exit /b 1
)

echo [%date% %time%] Regenerant episodis: %*

REM Actualitza el repo
if not exist "%WORKDIR%\.git" (
    git clone "%REPO_URL%" "%WORKDIR%"
) else (
    cd /d "%WORKDIR%"
    git remote set-url origin "%REPO_URL%"
    git fetch -q origin main
    git reset -q --hard origin/main
)

cd /d "%WORKDIR%"
set "REPO_DIR=%WORKDIR%"
py "%WORKDIR%\veu\regenera_pc.py" %*
if errorlevel 1 (
    echo [%date% %time%] La regeneracio ha acabat amb errors.
    exit /b 1
)
echo [%date% %time%] Regeneracio completada.
exit /b 0
