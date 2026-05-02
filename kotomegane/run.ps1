Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$envFile = Join-Path $PSScriptRoot ".env"
$pyvenvConfig = Join-Path $PSScriptRoot ".venv\pyvenv.cfg"

if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Virtual environment not found. Run .\setup.ps1 first."
}

function Get-KeySourceMessage {
    param(
        [Parameter(Mandatory = $true)]
        [string]$EnvVar
    )

    $envFileValue = ""
    if (Test-Path -LiteralPath $envFile) {
        foreach ($line in Get-Content -LiteralPath $envFile) {
            if ($line -match ("^\s*" + [regex]::Escape($EnvVar) + "\s*=\s*(.+?)\s*$")) {
                $envFileValue = $Matches[1].Trim()
                break
            }
        }
    }

    $processValue = [Environment]::GetEnvironmentVariable($EnvVar, "Process")
    $userValue = [Environment]::GetEnvironmentVariable($EnvVar, "User")
    $machineValue = [Environment]::GetEnvironmentVariable($EnvVar, "Machine")

    if (-not [string]::IsNullOrWhiteSpace($envFileValue) -and -not [string]::IsNullOrWhiteSpace($processValue) -and $envFileValue -ne $processValue) {
        return "${EnvVar} source: environment variable (takes precedence over .env)."
    }
    if (-not [string]::IsNullOrWhiteSpace($envFileValue)) {
        return "${EnvVar} source: .env"
    }
    if (-not [string]::IsNullOrWhiteSpace($userValue)) {
        return "${EnvVar} source: user environment"
    }
    if (-not [string]::IsNullOrWhiteSpace($machineValue)) {
        return "${EnvVar} source: machine environment"
    }
    if (-not [string]::IsNullOrWhiteSpace($processValue)) {
        return "${EnvVar} source: current process environment"
    }
    return $null
}

function Get-VenvBaseInterpreter {
    if (-not (Test-Path -LiteralPath $pyvenvConfig)) {
        return $null
    }

    foreach ($line in Get-Content -LiteralPath $pyvenvConfig) {
        if ($line -match '^\s*executable\s*=\s*(.+?)\s*$') {
            return $Matches[1].Trim()
        }
    }

    return $null
}

function Start-KotomeganeRuntime {
    $appPath = Join-Path $PSScriptRoot "app.py"
    $commandLine = 'cmd.exe /d /s /c ""{0}" "{1}""' -f $venvPython, $appPath

    if (-not ("KotomeganeRuntimeHost" -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;

public static class KotomeganeRuntimeHost {
    [StructLayout(LayoutKind.Sequential)]
    public struct IO_COUNTERS {
        public ulong ReadOperationCount;
        public ulong WriteOperationCount;
        public ulong OtherOperationCount;
        public ulong ReadTransferCount;
        public ulong WriteTransferCount;
        public ulong OtherTransferCount;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct JOBOBJECT_BASIC_LIMIT_INFORMATION {
        public long PerProcessUserTimeLimit;
        public long PerJobUserTimeLimit;
        public uint LimitFlags;
        public UIntPtr MinimumWorkingSetSize;
        public UIntPtr MaximumWorkingSetSize;
        public uint ActiveProcessLimit;
        public UIntPtr Affinity;
        public uint PriorityClass;
        public uint SchedulingClass;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct JOBOBJECT_EXTENDED_LIMIT_INFORMATION {
        public JOBOBJECT_BASIC_LIMIT_INFORMATION BasicLimitInformation;
        public IO_COUNTERS IoInfo;
        public UIntPtr ProcessMemoryLimit;
        public UIntPtr JobMemoryLimit;
        public UIntPtr PeakProcessMemoryUsed;
        public UIntPtr PeakJobMemoryUsed;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct STARTUPINFO {
        public uint cb;
        public string lpReserved;
        public string lpDesktop;
        public string lpTitle;
        public uint dwX;
        public uint dwY;
        public uint dwXSize;
        public uint dwYSize;
        public uint dwXCountChars;
        public uint dwYCountChars;
        public uint dwFillAttribute;
        public uint dwFlags;
        public ushort wShowWindow;
        public ushort cbReserved2;
        public IntPtr lpReserved2;
        public IntPtr hStdInput;
        public IntPtr hStdOutput;
        public IntPtr hStdError;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct PROCESS_INFORMATION {
        public IntPtr hProcess;
        public IntPtr hThread;
        public uint dwProcessId;
        public uint dwThreadId;
    }

    private const int JobObjectExtendedLimitInformation = 9;
    private const uint JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000;
    private const uint CREATE_SUSPENDED = 0x00000004;
    private const uint STARTF_USESTDHANDLES = 0x00000100;
    private const uint INFINITE = 0xFFFFFFFF;
    private const int STD_INPUT_HANDLE = -10;
    private const int STD_OUTPUT_HANDLE = -11;
    private const int STD_ERROR_HANDLE = -12;

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern IntPtr CreateJobObject(IntPtr lpJobAttributes, string lpName);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool SetInformationJobObject(IntPtr hJob, int infoType, IntPtr lpJobObjectInfo, uint cbJobObjectInfoLength);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CreateProcessW(
        string applicationName,
        string commandLine,
        IntPtr processAttributes,
        IntPtr threadAttributes,
        bool inheritHandles,
        uint creationFlags,
        IntPtr environment,
        string currentDirectory,
        ref STARTUPINFO startupInfo,
        out PROCESS_INFORMATION processInformation
    );

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern uint ResumeThread(IntPtr thread);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool GetExitCodeProcess(IntPtr process, out uint exitCode);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool CloseHandle(IntPtr handle);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr GetStdHandle(int handleId);

    public static int RunInKillOnCloseJob(string commandLine, string currentDirectory) {
        IntPtr job = IntPtr.Zero;
        PROCESS_INFORMATION processInfo = new PROCESS_INFORMATION();
        bool processCreated = false;

        try {
            job = CreateKillOnCloseJob();

            STARTUPINFO startupInfo = new STARTUPINFO();
            startupInfo.cb = (uint)Marshal.SizeOf(typeof(STARTUPINFO));
            startupInfo.dwFlags = STARTF_USESTDHANDLES;
            startupInfo.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
            startupInfo.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
            startupInfo.hStdError = GetStdHandle(STD_ERROR_HANDLE);

            if (!CreateProcessW(
                null,
                commandLine,
                IntPtr.Zero,
                IntPtr.Zero,
                true,
                CREATE_SUSPENDED,
                IntPtr.Zero,
                currentDirectory,
                ref startupInfo,
                out processInfo
            )) {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }

            processCreated = true;

            if (!AssignProcessToJobObject(job, processInfo.hProcess)) {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }

            if (ResumeThread(processInfo.hThread) == 0xFFFFFFFF) {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }

            WaitForSingleObject(processInfo.hProcess, INFINITE);

            uint exitCode;
            if (!GetExitCodeProcess(processInfo.hProcess, out exitCode)) {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }

            return unchecked((int)exitCode);
        }
        finally {
            if (processCreated) {
                if (processInfo.hThread != IntPtr.Zero) {
                    CloseHandle(processInfo.hThread);
                }
                if (processInfo.hProcess != IntPtr.Zero) {
                    CloseHandle(processInfo.hProcess);
                }
            }
            if (job != IntPtr.Zero) {
                CloseHandle(job);
            }
        }
    }

    private static IntPtr CreateKillOnCloseJob() {
        IntPtr job = CreateJobObject(IntPtr.Zero, null);
        if (job == IntPtr.Zero) {
            throw new Win32Exception(Marshal.GetLastWin32Error());
        }

        JOBOBJECT_EXTENDED_LIMIT_INFORMATION info = new JOBOBJECT_EXTENDED_LIMIT_INFORMATION();
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;

        IntPtr pointer = Marshal.AllocHGlobal(Marshal.SizeOf(typeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION)));
        try {
            Marshal.StructureToPtr(info, pointer, false);
            if (!SetInformationJobObject(job, JobObjectExtendedLimitInformation, pointer, (uint)Marshal.SizeOf(typeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION)))) {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }
        }
        finally {
            Marshal.FreeHGlobal(pointer);
        }

        return job;
    }
}
'@
    }

    return [KotomeganeRuntimeHost]::RunInKillOnCloseJob($commandLine, $PSScriptRoot)
}

$providerEnvVars = @("OPENAI_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY")
$keyStatuses = @(
    $providerEnvVars | ForEach-Object { Get-KeySourceMessage -EnvVar $_ } | Where-Object { $null -ne $_ }
)
if ($keyStatuses.Count -eq 0) {
    throw "No provider API key was found. Set OPENAI_API_KEY, GEMINI_API_KEY, or ANTHROPIC_API_KEY in .env or in your environment before running .\run.ps1."
}

foreach ($keyStatus in $keyStatuses) {
    Write-Host $keyStatus
}
$baseInterpreter = Get-VenvBaseInterpreter
Write-Host "Runtime python launcher: $venvPython"
if ($baseInterpreter) {
    Write-Host "Venv base interpreter: $baseInterpreter"
}
Write-Host "Stop command: Ctrl+C or .\\stop.ps1"
exit (Start-KotomeganeRuntime)
