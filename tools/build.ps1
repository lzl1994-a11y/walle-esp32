param(
    [ValidateSet("build", "reconfigure", "flash", "monitor", "size")]
    [string]$Target = "build",
    [string]$Port = "",
    [string]$IdfPath = "D:\Espressif\frameworks\esp-idf-v5.5.4",
    [string]$ToolsPath = "D:\Espressif"
)
$ErrorActionPreference = "Stop"
if (-not $env:PROCESSOR_ARCHITECTURE) { $env:PROCESSOR_ARCHITECTURE = "AMD64" }
$env:IDF_TOOLS_PATH = $ToolsPath
$env:IDF_PYTHON_ENV_PATH = Join-Path $ToolsPath "python_env\idf5.5_py3.11_env"
. (Join-Path $IdfPath "export.ps1")
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    $idfArguments = @()
    if ($Port) { $idfArguments += @("-p", $Port) }
    if ($Target -in @("flash", "monitor") -and -not $Port) {
        throw "Specify -Port for flash/monitor; confirm the audio has been rewired first."
    }
    $idfArguments += $Target
    idf.py @idfArguments
    if ($LASTEXITCODE -ne 0) { throw "ESP-IDF $Target failed ($LASTEXITCODE)" }
} finally { Pop-Location }
