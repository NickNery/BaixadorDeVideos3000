$ErrorActionPreference = "Stop"

$binRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$repoRoot = Resolve-Path (Join-Path $binRoot "..")
$winRoot = Join-Path $repoRoot "Win"
$macRoot = Join-Path $repoRoot "Mac"
$winBin = Join-Path $winRoot "Bin"
$macBin = Join-Path $macRoot "Bin"

function Remove-InsideRepo {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    $repo = (Resolve-Path -LiteralPath $repoRoot).Path
    $resolved = (Resolve-Path -LiteralPath $Path).Path
    if (-not $resolved.StartsWith($repo, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Recusei remover fora do repositorio: $resolved"
    }
    Remove-Item -LiteralPath $resolved -Recurse -Force
}

function Copy-BinBase {
    param(
        [Parameter(Mandatory = $true)][string]$TargetBin,
        [Parameter(Mandatory = $true)][string[]]$ExcludedFiles
    )

    New-Item -ItemType Directory -Force -Path $TargetBin | Out-Null
    robocopy $binRoot $TargetBin /E /R:2 /W:2 /NFL /NDL /NJH /NJS `
        /XD build node_modules dist-packages .venv __pycache__ `
        /XF package-lock.json $ExcludedFiles | Out-Null
    if ($LASTEXITCODE -ge 8) {
        throw "Falha ao copiar Bin para $TargetBin"
    }
}

function Copy-RootFiles {
    param([Parameter(Mandatory = $true)][string]$TargetRoot)

    Copy-Item -LiteralPath (Join-Path $repoRoot "README.md") -Destination (Join-Path $TargetRoot "README.md") -Force
    Copy-Item -LiteralPath (Join-Path $repoRoot "update_manifest.json") -Destination (Join-Path $TargetRoot "update_manifest.json") -Force
}

function Remove-ChildrenByPattern {
    param(
        [Parameter(Mandatory = $true)][string]$BasePath,
        [Parameter(Mandatory = $true)][string[]]$Patterns
    )

    foreach ($pattern in $Patterns) {
        Get-ChildItem -LiteralPath $BasePath -Recurse -Force -File -Filter $pattern -ErrorAction SilentlyContinue |
            ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force }
    }
}

Remove-InsideRepo $winRoot
Remove-InsideRepo $macRoot

New-Item -ItemType Directory -Force -Path `
    $winRoot, (Join-Path $winRoot "setup"), `
    $macRoot, (Join-Path $macRoot "setup") | Out-Null

Copy-BinBase $winBin @(
    "*.command",
    "*.zsh",
    "Baixador_YTDLP_Windows_macOS.zip",
    "BaixadorDeVideos3000_Instalador_macOS.zip",
    "BaixadorDeVideos3000_Setup_Windows.exe",
    "BaixadorDeVideos3000_macOS.dmg",
    "Instalador_Automatico_macOS.command",
    "TUTORIAL_DISTRIBUICAO_WINDOWS_MACOS.md"
)

Copy-BinBase $macBin @(
    "*.exe",
    "*.bat",
    "*.ps1",
    "*.vbs",
    "*.ico",
    "yt-dlp.exe",
    "Baixador_YTDLP_Windows_macOS.zip",
    "BaixadorDeVideos3000_Instalador_macOS.zip",
    "BaixadorDeVideos3000_Setup_Windows.exe",
    "TUTORIAL_DISTRIBUICAO_WINDOWS_MACOS.md"
)

Remove-ChildrenByPattern $macBin @("electron_launcher.py")

Copy-RootFiles $winRoot
Copy-RootFiles $macRoot

Copy-Item -LiteralPath (Join-Path $repoRoot "setup\setup_installer.py") -Destination (Join-Path $winRoot "setup\setup_installer.py") -Force
Copy-Item -LiteralPath (Join-Path $repoRoot "setup\Setup_BaixadorDeVideos3000_Windows.exe") -Destination (Join-Path $winRoot "setup\Setup_BaixadorDeVideos3000_Windows.exe") -Force

Copy-Item -LiteralPath (Join-Path $repoRoot "setup\Setup_BaixadorDeVideos3000_macOS.command") -Destination (Join-Path $macRoot "setup\Setup_BaixadorDeVideos3000_macOS.command") -Force
Copy-Item -LiteralPath (Join-Path $repoRoot "setup\Limpar_BaixadorDeVideos3000_macOS.command") -Destination (Join-Path $macRoot "setup\Limpar_BaixadorDeVideos3000_macOS.command") -Force

Write-Host "Distribuicao preparada:"
Write-Host " - $winRoot"
Write-Host " - $macRoot"
