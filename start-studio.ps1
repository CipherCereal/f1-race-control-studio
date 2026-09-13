$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$studioPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $studioPython)) { throw 'Run setup.ps1 first.' }
try {
  $studioState = Invoke-RestMethod 'http://127.0.0.1:8765/api/state' -TimeoutSec 2
  Write-Output 'Ghost Rival Studio is already running at http://127.0.0.1:8765'
} catch {
  Start-Process -FilePath $studioPython -ArgumentList '-m uvicorn backend.main:app --host 127.0.0.1 --port 8765' -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $PSScriptRoot 'data\reports\server.log') -RedirectStandardError (Join-Path $PSScriptRoot 'data\reports\server-errors.log')
  Write-Output 'Ghost Rival Studio started at http://127.0.0.1:8765'
}
