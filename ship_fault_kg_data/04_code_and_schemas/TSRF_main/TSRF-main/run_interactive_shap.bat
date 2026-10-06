@echo off
chcp 65001 >nul
REM Run interactive SHAP analysis tool using conda environment
REM Solves "No module named 'shap'" issue

echo ============================================================
echo Interactive SHAP Analysis Tool
echo ============================================================
echo.
echo Running with conda environment...
echo.

REM Switch to script directory
cd /d "%~dp0"

REM Run Python script using conda environment
D:\Anaconda\Scripts\conda.exe run -p "d:\Pycharm_Project\Pytorch\NSFC\Data-test-3\.conda" --no-capture-output python interactive_shap.py

echo.
echo ============================================================
echo Done!
echo ============================================================
pause
