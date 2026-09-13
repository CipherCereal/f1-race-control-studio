$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
& '.\.venv\Scripts\python.exe' -m pip install --ignore-installed 'torch==2.11.0+cu128' 'torchvision==0.26.0+cu128' --index-url https://download.pytorch.org/whl/cu128 --no-deps
if ($LASTEXITCODE -ne 0) { throw 'CUDA installation failed.' }
& '.\.venv\Scripts\python.exe' -c 'from backend.compute import compute_status; print(compute_status())'
