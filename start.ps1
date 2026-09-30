$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (!(Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Instale o Python 3.12 ou superior e tente novamente.' }
    & '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Falha na instalação das dependências.' }
}
Write-Host 'Acesse http://127.0.0.1:8080 no navegador.' -ForegroundColor Green
& '.\.venv\Scripts\python.exe' app.py
