@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
title FatOutFitIn
where py >nul 2>nul
if not errorlevel 1 (
    py -3 iniciar.py %*
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo Python nao encontrado. Instale Python 3.10 ou superior.
        echo https://www.python.org/downloads/windows/
        echo Consulte GUIA-PARA-RODAR.md nesta pasta.
        pause
        exit /b 1
    )
    python iniciar.py %*
)
if errorlevel 1 (
    echo.
    echo Nao foi possivel iniciar. Confira a mensagem acima e a pasta .local\logs.
    pause
    exit /b 1
)
