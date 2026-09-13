$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:STUDIO_PRESERVE_RUNNING_JOBS='1'
try { Invoke-RestMethod 'http://127.0.0.1:8767/api/compute' -TimeoutSec 2 | Out-Null }
catch { Start-Process -FilePath (Join-Path $PSScriptRoot '.venv\Scripts\python.exe') -ArgumentList '-m uvicorn backend.main:app --host 127.0.0.1 --port 8767' -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput 'data/reports/curved-server.log' -RedirectStandardError 'data/reports/curved-server-errors.log' }
Remove-Item Env:STUDIO_PRESERVE_RUNNING_JOBS
