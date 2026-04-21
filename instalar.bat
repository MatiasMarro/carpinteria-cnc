@echo off
echo ====================================================================
echo   CARPINTERIA 2.0 - INSTALACION
echo ====================================================================
echo.

echo [1/3] Verificando Python...
python --version
if errorlevel 1 (
    echo ERROR: Python no esta instalado
    pause
    exit /b 1
)

echo.
echo [2/3] Instalando dependencias...
pip install -r requirements.txt

echo.
echo [3/3] Verificando instalacion...
python cli.py listar

echo.
echo ====================================================================
echo   INSTALACION COMPLETADA
echo ====================================================================
echo.
echo Proximos pasos:
echo   1. Ejecuta: python cli.py usar escritorio_estandar --exportar
echo   2. Los DXF se generaran en la carpeta output/
echo   3. Importa esos DXF en Vectric Aspire
echo.
pause
