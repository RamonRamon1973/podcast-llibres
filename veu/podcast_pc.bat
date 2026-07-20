@echo off
REM ============================================================
REM  podcast_pc.bat - Genera l'audio dels episodis amb Azure
REM  S'executa cada dia des de l'Administrador de tasques.
REM  Cal editar les 4 variables de sota amb les teves dades.
REM ============================================================

REM --- CONFIGURACIO (edita aixo) ---
set "GH_TOKEN=EL_TEU_TOKEN_DE_GITHUB"
set "AZURE_KEY=LA_TEVA_CLAU_AZURE"
set "AZURE_REGION=francecentral"
set "WORKDIR=%USERPROFILE%\podcast-gestio"
set "FFMPEG_DIR=C:\podcast"
REM ---------------------------------

set "AZURE_VOICE=ca-ES-JoanaNeural"
set "REPO_URL=https://x-access-token:%GH_TOKEN%@github.com/RamonRamon1973/podcast-llibres.git"

echo [%date% %time%] Iniciant proces del podcast...

REM Clona el repo si no existeix; si existeix, l'actualitza
if not exist "%WORKDIR%\.git" (
    echo Clonant el repositori per primera vegada...
    git clone "%REPO_URL%" "%WORKDIR%"
    if errorlevel 1 ( echo ERROR clonant el repo & exit /b 1 )
) else (
    cd /d "%WORKDIR%"
    git remote set-url origin "%REPO_URL%"
    git fetch -q origin main
    git reset -q --hard origin/main
)

cd /d "%WORKDIR%"

REM Executa el processador de guions pendents
set "REPO_DIR=%WORKDIR%"
py "%WORKDIR%\veu\processa_pendents.py"
if errorlevel 1 (
    echo [%date% %time%] El proces ha acabat amb errors. Revisa el missatge de dalt.
    exit /b 1
)

echo [%date% %time%] Proces completat correctament.
exit /b 0
