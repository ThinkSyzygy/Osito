[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArguments
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Creator = Join-Path $ScriptDir "create_project.py"

$PythonCommand = $null
if ($env:PYTHON) {
    $PythonCommand = $env:PYTHON
} else {
    foreach ($Candidate in @("python", "python3", "py")) {
        if (Get-Command $Candidate -ErrorAction SilentlyContinue) {
            $PythonCommand = $Candidate
            break
        }
    }
}

if (-not $PythonCommand) {
    Write-Error "Python 3 is required; no project was created."
    exit 2
}

& $PythonCommand $Creator @RemainingArguments
exit $LASTEXITCODE
