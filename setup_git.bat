@echo off
echo ====================================================================
echo   CARPINTERIA 2.0 - SETUP GIT + GITHUB
echo ====================================================================
echo.
echo Este script inicializa Git y prepara el repo para subirlo a GitHub.
echo.

echo [1/5] Verificando Git...
git --version
if errorlevel 1 (
    echo ERROR: Git no esta instalado.
    echo Descargar desde: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo.
echo [2/5] Inicializando repositorio Git...
git init

echo.
echo [3/5] Agregando archivos...
git add .

echo.
echo [4/5] Creando primer commit...
git commit -m "Initial commit: Sistema parametrico carpinteria CNC"

echo.
echo [5/5] Configurando rama main...
git branch -M main

echo.
echo ====================================================================
echo   GIT LISTO. AHORA:
echo ====================================================================
echo.
echo 1. Ve a: https://github.com/new
echo 2. Nombre del repo: carpinteria-cnc
echo 3. Click en "Create repository"
echo 4. Copia el comando que te da GitHub y pegalo aqui:
echo.
echo    Ejemplo:
echo    git remote add origin https://github.com/TU_USUARIO/carpinteria-cnc.git
echo    git push -u origin main
echo.
pause
