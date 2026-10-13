@echo off
setlocal enabledelayedexpansion

echo ==========================================================
echo  AtmosIQ Isolated ML Environment Setup ^& Evaluation
echo ==========================================================
echo This script creates an ISOLATED virtual environment (.venv_ml)
echo to prevent polluting the lightweight backend\.venv.

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set VENV_DIR=%PROJECT_ROOT%\.venv_ml
set ADAPTER_DIR=%PROJECT_ROOT%\backend\models\atmosiq-supervisor-lora-v2
set EVAL_SCRIPT=%PROJECT_ROOT%\data\training\evaluate_adapter_inference.py
set EVAL_DATA=%PROJECT_ROOT%\data\training\challenge_eval_25.jsonl
set REPORT_OUT=%PROJECT_ROOT%\data\training\challenge_eval_25_adapter_report.json

if not exist "%VENV_DIR%" (
    echo Creating isolated virtual environment at %VENV_DIR%...
    py -3.12 -m venv "%VENV_DIR%" || python -m venv "%VENV_DIR%"
) else (
    echo Existing isolated virtual environment detected at %VENV_DIR%.
)

set PY_ML=%VENV_DIR%\Scripts\python.exe

echo Installing ML dependencies into isolated environment...
"%PY_ML%" -m pip install --upgrade pip
"%PY_ML%" -m pip install torch --index-url https://download.pytorch.org/whl/cpu
"%PY_ML%" -m pip install transformers peft accelerate

echo Running standalone LoRA V2 inference on 25 challenge prompts...
"%PY_ML%" "%EVAL_SCRIPT%" ^
    --base-model "Qwen/Qwen2.5-0.5B-Instruct" ^
    --adapter-dir "%ADAPTER_DIR%" ^
    --eval-file "%EVAL_DATA%" ^
    --output-file "%REPORT_OUT%" ^
    --device "cpu"

echo Evaluation finished! Report saved to %REPORT_OUT%.
pause
