param(
    [int]$Port = 8083
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$appPath = Join-Path $PSScriptRoot "app.py"

function Get-ProcessTable {
    $table = @{}
    foreach ($process in Get-CimInstance Win32_Process) {
        $table[[int]$process.ProcessId] = $process
    }
    return $table
}

function Get-KotomeganeStopRootPid {
    param(
        [int]$OwningProcess,
        [hashtable]$ProcessTable
    )

    $selectedPid = $OwningProcess
    if (-not $ProcessTable.ContainsKey($OwningProcess)) {
        return $selectedPid
    }

    $cursor = $ProcessTable[$OwningProcess]
    while ($null -ne $cursor) {
        $parentPid = [int]$cursor.ParentProcessId
        if ($parentPid -le 0 -or -not $ProcessTable.ContainsKey($parentPid)) {
            break
        }

        $parent = $ProcessTable[$parentPid]
        $parentPath = [string]$parent.ExecutablePath
        $parentCommandLine = [string]$parent.CommandLine

        $isKotomeganePython = $false
        if (-not [string]::IsNullOrWhiteSpace($parentPath)) {
            $isKotomeganePython = $parentPath.Equals($venvPython, [System.StringComparison]::OrdinalIgnoreCase)
        }
        if (-not $isKotomeganePython -and -not [string]::IsNullOrWhiteSpace($parentCommandLine)) {
            $isKotomeganePython = $parentCommandLine.IndexOf($appPath, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
        }
        if (-not $isKotomeganePython) {
            break
        }

        $selectedPid = $parentPid
        $cursor = $parent
    }

    return $selectedPid
}

$listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($null -eq $listener) {
    Write-Host "No listener found on port $Port."
    exit 0
}

$processTable = Get-ProcessTable
$ownerPid = [int]$listener.OwningProcess
$rootPid = Get-KotomeganeStopRootPid -OwningProcess $ownerPid -ProcessTable $processTable

$ownerProcess = $null
if ($processTable.ContainsKey($ownerPid)) {
    $ownerProcess = $processTable[$ownerPid]
}
$rootProcess = $null
if ($processTable.ContainsKey($rootPid)) {
    $rootProcess = $processTable[$rootPid]
}

Write-Host "Stopping Kotomegane on port $Port"
Write-Host "Listener PID: $ownerPid"
if ($ownerProcess -and $ownerProcess.ExecutablePath) {
    Write-Host "Listener executable: $($ownerProcess.ExecutablePath)"
}
if ($rootPid -ne $ownerPid) {
    Write-Host "Root PID: $rootPid"
    if ($rootProcess -and $rootProcess.ExecutablePath) {
        Write-Host "Root executable: $($rootProcess.ExecutablePath)"
    }
}

$taskkillOutput = & taskkill /PID $rootPid /T /F 2>&1
if ($taskkillOutput) {
    $taskkillOutput | ForEach-Object { Write-Host $_ }
}

Start-Sleep -Seconds 1
$remaining = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($remaining) {
    throw "Port $Port is still listening after stop attempt."
}

Write-Host "Port $Port stopped."
