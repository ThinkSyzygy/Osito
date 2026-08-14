[CmdletBinding()]
param(
    [string]$Root = ".",
    [string]$Denylist,
    [int]$MaxFileBytes = 1000000,
    [switch]$Json
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Scanner = Join-Path $ScriptDir "sanitize.py"

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
    Write-Error "Python 3 is required; no audit was run."
    exit 2
}

$Arguments = @($Scanner, "--root", $Root, "--max-file-bytes", "$MaxFileBytes")
if ($Denylist) {
    $Arguments += @("--denylist", $Denylist)
}
if ($Json) {
    $Arguments += "--json"
}

& $PythonCommand @Arguments
exit $LASTEXITCODE
