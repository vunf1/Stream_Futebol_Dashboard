# deploy.ps1

param (
    [string]$BuildScript = ".\build.py",
    [string]$DistFolder  = ".\dist",
    [string]$ExeName     = "goal_score.exe",
    [string]$TargetRoot  = "$Env:USERPROFILE\Desktop\OBS_MARCADOR_FUTEBOL\futebol-dashboard",
    [string]$TargetExe   = "Futebol Dashboard.exe",
    [string]$IconSource  = ".\assets\icons",
    [string]$IconTarget  = "assets\icons"
)

# Guarda o diretório inicial
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $scriptDir

try {
    Write-Host "1) Executando build: python $BuildScript"
    python $BuildScript -ErrorAction Stop

    # Certifica-se de que a pasta de destino existe
    Write-Host "2) Criando pasta de destino: $TargetRoot"
    New-Item -ItemType Directory -Path $TargetRoot -Force | Out-Null

    # Copia do executável
    $sourceExe = Join-Path $DistFolder $ExeName
    $destExe   = Join-Path $TargetRoot $TargetExe
    Write-Host "3) Copiando EXE: $sourceExe → $destExe"
    Copy-Item -Path $sourceExe -Destination $destExe -Force -ErrorAction Stop

    # Copia da pasta de ícones
    $sourceIcons = Resolve-Path $IconSource
    $destIcons   = Join-Path $TargetRoot $IconTarget
    Write-Host "4) Copiando ícones: $sourceIcons → $destIcons"
    Copy-Item -Path $sourceIcons -Destination $destIcons -Recurse -Force -ErrorAction Stop

    Write-Host "✅ Deploy concluído com sucesso!"
}
catch {
    Write-Error "❌ Ocorreu um erro: $_"
}
finally {
    # Volta ao diretório original
    Pop-Location
    Write-Host "Retornado para $PWD"
}
