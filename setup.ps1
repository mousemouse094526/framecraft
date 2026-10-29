# framecraft setup for Windows, started by setup.cmd. Installs uv if needed,
# syncs the venv, then hands everything else (models, checklist) to
# `python -m backend.setup`.
# ASCII only: Windows PowerShell 5.1 reads a UTF-8 file without a BOM as the
# ANSI code page. Thai text is printed from Python.
# No $ErrorActionPreference = 'Stop': with stderr redirected, PowerShell 5.1
# turns uv's progress output into errors. Exit codes are checked instead.
Set-Location -LiteralPath $PSScriptRoot -ErrorAction Stop

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host 'Installing uv...'
    # A child process: the installer ends with `exit`, and it refuses to run
    # unless the session's execution policy allows scripts. Older Windows 10
    # doesn't offer TLS 1.2 by default.
    powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12; irm https://astral.sh/uv/0.13.6/install.ps1 | iex"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    # The installer adds uv to the user PATH for new windows only; it picks the first of these.
    $uvBin = if ($env:XDG_BIN_HOME) { $env:XDG_BIN_HOME }
        elseif ($env:XDG_DATA_HOME) { Join-Path $env:XDG_DATA_HOME '..\bin' }
        else { Join-Path $HOME '.local\bin' }
    $env:Path = "$uvBin;$env:Path"
}

# npm installs the web UI and npm run dev starts it.
if (-not (Get-Command node -ErrorAction SilentlyContinue) -or
    -not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host 'Node.js 22+ required: https://nodejs.org'
    exit 1
}

uv sync
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
# PYTHONUTF8: setup prints Thai. --no-sync: uv sync above already installed everything.
$env:PYTHONUTF8 = '1'
uv run --no-sync python -m backend.setup
exit $LASTEXITCODE
