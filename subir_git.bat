@echo off
cd /d "C:\Users\nlfer\Desktop\Proyectos\Fondos\Dashboard_FFMM"

REM Configurar identidad de Git si no está seteada
git config --global user.name >nul 2>&1
IF ERRORLEVEL 1 (
    git config --global user.name "nlfernan"
)

git config --global user.email >nul 2>&1
IF ERRORLEVEL 1 (
    git config --global user.email "nlfernansam@gmail.com"
)

REM Inicializar repositorio Git si no existe
IF NOT EXIST ".git" (
    echo Inicializando repositorio Git...
    git init
    git branch -M main
)

REM Configurar remote origin
git remote get-url origin >nul 2>&1
IF ERRORLEVEL 1 (
    echo Enlazando con GitHub...
    git remote add origin https://github.com/nlfernan/dashboard-fondos-mutuo.git
) ELSE (
    echo Remote origin ya existe, actualizando URL...
    git remote set-url origin https://github.com/nlfernan/dashboard-fondos-mutuo.git
)

REM Agregar archivos y hacer commit con timestamp
git add .

set hour=%time:~0,2%
if "%hour:~0,1%"==" " set hour=0%hour:~1,1%
git commit -m "Actualizacion automatica %date% %hour%:%time:~3,2%"

REM Subir cambios al repositorio remoto
git push -u origin main

pause
