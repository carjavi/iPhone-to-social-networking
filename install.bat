@echo off
title Instalando las dependencias necesarias...
echo --- Configurando entorno virtual ---

:: 1. Verificar si existe la carpeta venv
if exist "venv\" (
    echo [OK] Carpeta 'venv' detectada.
) else (
    echo [AVISO] No se encontro la carpeta 'venv'. Creandola ahora...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual. Verifica tu instalacion de Python.
        pause
        exit /b
    )
    echo [OK] Entorno virtual creado exitosamente.
)

echo.
echo --- Instalando librerias DENTRO de venv ---

:: Actualizar pip
".\venv\Scripts\python.exe" -m pip install --upgrade pip

:: Instalar Pillow (Procesamiento de imagenes basico)
echo Instalando Pillow...
".\venv\Scripts\pip.exe" install Pillow

:: Instalar pillow-heif (Necesario para leer archivos .HEIC de iPhone)
echo Instalando pillow-heif...
".\venv\Scripts\pip.exe" install pillow-heif

echo.
echo --- Todo listo ---
echo Las librerias (Pillow y pillow-heif) se han instalado correctamente en 'venv'.
echo recuerda activar el entorno virtual antes de ejecutar el script principal desde el terminal de Gitbash 
echo source venv/Scripts/activate 
echo.
pause

:: Comando de autodestrucción
(goto) 2>nul & del "%~f0"