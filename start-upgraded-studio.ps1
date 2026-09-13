$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:STUDIO_PRESERVE_RUNNING_JOBS = '1'
try {
  Invoke-RestMethod 'http://127.0.0.1:8766/api/compute' -TimeoutSec 2 | Out-Null
} catch {
  Start-Process -FilePath (Join-Path $PSScriptRoot '.venv\Scripts\python.exe') -ArgumentList '-m uvicorn backend.main:app --host 127.0.0.1 --port 8766' -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $PSScriptRoot 'data\reports\upgraded-server.log') -RedirectStandardError (Join-Path $PSScriptRoot 'data\reports\upgraded-server-errors.log')
}
Remove-Item Env:STUDIO_PRESERVE_RUNNING_JOBS
Write-Output 'Upgraded Studio: http://127.0.0.1:8766 — existing workers preserved.'
