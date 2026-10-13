# AtmosIQ — Setup Isolated ML Virtual Environment for LoRA V2 Inference
# This script creates a SEPARATE virtual environment (.venv_ml) so that backend/.venv remains clean and untouched.

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
$VenvDir = Join-Path $ProjectRoot ".venv_ml"
$AdapterDir = Join-Path $ProjectRoot "backend\models\atmosiq-supervisor-lora-v2"
$EvalScript = Join-Path $ProjectRoot "data\training\evaluate_adapter_inference.py"
$EvalData = Join-Path $ProjectRoot "data\training\challenge_eval_25.jsonl"
$ReportOut = Join-Path $ProjectRoot "data\training\challenge_eval_25_adapter_report.json"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " AtmosIQ Isolated ML Environment Setup & LoRA V2 Evaluation" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Project Root: $ProjectRoot"
Write-Host "Target ML Venv: $VenvDir (Isolated from backend\.venv)"
Write-Host "LoRA Adapter: $AdapterDir"

# 1. Locate available Python (Python 3.12 or 3.11 preferred for PyTorch stability)
$PyLauncher = Get-Command "py" -ErrorAction SilentlyContinue
if ($PyLauncher) {
    Write-Host "Using Python launcher to select Python 3.12/3.11..." -ForegroundColor Yellow
    $PyCmd = "py -3.12"
} else {
    $PyCmd = "python"
}

# 2. Create isolated virtual environment if it doesn't already exist
if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating isolated virtual environment at $VenvDir..." -ForegroundColor Green
    & py -3.12 -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Falling back to default python interpreter..." -ForegroundColor Yellow
        & python -m venv $VenvDir
    }
} else {
    Write-Host "Existing isolated virtual environment found at $VenvDir." -ForegroundColor Green
}

$PyML = Join-Path $VenvDir "Scripts\python.exe"

# 3. Upgrade pip and install isolated ML dependencies
Write-Host "Installing PyTorch, Transformers, PEFT, and Accelerate into isolated venv..." -ForegroundColor Green
& $PyML -m pip install --upgrade pip
# Install CPU or CUDA PyTorch
& $PyML -m pip install torch --index-url https://download.pytorch.org/whl/cpu
& $PyML -m pip install transformers peft accelerate

# 4. Run standalone inference evaluation on 25 challenge prompts
Write-Host "Running isolated adapter inference on 25 challenge prompts..." -ForegroundColor Green
& $PyML $EvalScript `
    --base-model "Qwen/Qwen2.5-0.5B-Instruct" `
    --adapter-dir $AdapterDir `
    --eval-file $EvalData `
    --output-file $ReportOut `
    --device "cpu"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Evaluation completed! Check report at: $ReportOut" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
