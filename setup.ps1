$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$srv = Join-Path $PSScriptRoot "server.py"

if (Get-Command claude -ErrorAction SilentlyContinue) {
    claude mcp add --scope user localScreenControl -- $py $srv
    Write-Host "Registered with Claude Code."
}

Write-Host "`nMCP client config (e.g. Claude Desktop):"
@{ mcpServers = @{ localScreenControl = @{ command = $py; args = @($srv) } } } | ConvertTo-Json -Depth 5
