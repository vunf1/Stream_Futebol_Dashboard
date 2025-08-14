# deploy.ps1
#Requires -Version 5.1
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'Low')]
param(
    [Parameter()][ValidateNotNullOrEmpty()][string]$BuildScript = ".\build.py",
    [Parameter()][ValidateNotNullOrEmpty()][string]$DistFolder  = ".\dist",
    [Parameter()][ValidateNotNullOrEmpty()][string]$ExeName     = "Apitofinal.exe",
    [Parameter()][ValidateNotNullOrEmpty()][string]$TargetRoot  = "$Env:USERPROFILE\Desktop\FUTEBOL-SCORE-DASHBOARD\",
    [Parameter()][ValidateNotNullOrEmpty()][string]$TargetExe   = "Apito Final.exe"
)

$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion.Major -ge 7) { $PSNativeCommandUseErrorActionPreference = $true }

$scriptRoot = Split-Path -LiteralPath $PSCommandPath
Push-Location -LiteralPath $scriptRoot
try {
    Write-Host "1) Building -> $BuildScript"

    # Prefer venv python if available, else fall back to PATH
    $venvPy = Join-Path $scriptRoot ".venv\Scripts\python.exe"
    if (Test-Path $venvPy) {
        $py = $venvPy
    } else {
        $py = "python"
    }
    & $py $BuildScript
    if ($LASTEXITCODE -ne 0) { throw "Build script failed with exit code $LASTEXITCODE." }

    Write-Host "2) Ensuring target folder -> $TargetRoot"
    New-Item -ItemType Directory -Path $TargetRoot -Force | Out-Null

    $sourceExe = Join-Path -Path $DistFolder -ChildPath $ExeName
    if (-not (Test-Path -LiteralPath $sourceExe)) {
        throw "Executable not found at '$sourceExe'."
    }

    $destExe = Join-Path -Path $TargetRoot -ChildPath $TargetExe

    $copyNeeded = $true
    if (Test-Path -LiteralPath $destExe) {
        $src = Get-Item -LiteralPath $sourceExe
        $dst = Get-Item -LiteralPath $destExe
        # Fast comparison: size + timestamp
        $copyNeeded = ($src.Length -ne $dst.Length) -or ($src.LastWriteTimeUtc -ne $dst.LastWriteTimeUtc)
    }

    if ($copyNeeded) {
        if ($PSCmdlet.ShouldProcess($destExe, "Copy from $sourceExe")) {
            Write-Host "3) Copying EXE -> $destExe"
            Copy-Item -LiteralPath $sourceExe -Destination $destExe -Force
        }
    } else {
        Write-Host "3) EXE unchanged - skipping copy."
    }

    Write-Host "Deploy concluido."
}
catch {
    Write-Error "Erro: $($_.Exception.Message)"
    exit 1
}
finally {
    Pop-Location
    Write-Host "<- Returned to $((Get-Location).Path)"
}
