# This installs uv

powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"

# Prompt and wait for any key press
Write-Host "`nType any key to terminate..."
[void][System.Console]::ReadKey($true)
