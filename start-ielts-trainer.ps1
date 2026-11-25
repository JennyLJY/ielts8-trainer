$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
Set-Location -LiteralPath $PSScriptRoot

Start-Job -ScriptBlock {
    Start-Sleep -Seconds 2
    Start-Process 'http://127.0.0.1:8088'
} | Out-Null

& "$PSScriptRoot\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8088
exit $LASTEXITCODE
