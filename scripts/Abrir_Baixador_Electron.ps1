$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Windows.Forms

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$electronDir = Join-Path $root "electron"
$logFile = Join-Path $root "BaixadorDeVideos3000_Electron.log"

function Show-Info($message) {
    [System.Windows.Forms.MessageBox]::Show($message, "Baixador de Videos 3000 - Electron", "OK", "Information") | Out-Null
}

function Show-Error($message) {
    [System.Windows.Forms.MessageBox]::Show($message, "Baixador de Videos 3000 - Electron", "OK", "Error") | Out-Null
}

function Ask-YesNo($message) {
    $result = [System.Windows.Forms.MessageBox]::Show($message, "Baixador de Videos 3000 - Electron", "YesNo", "Question")
    return $result -eq [System.Windows.Forms.DialogResult]::Yes
}

function Add-PathIfExists($path) {
    if ($path -and (Test-Path -LiteralPath $path)) {
        if (($env:PATH -split ";") -notcontains $path) {
            $env:PATH = "$path;$env:PATH"
        }
    }
}

function Refresh-NodePath {
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:PATH = "$machinePath;$userPath;$env:PATH"
    Add-PathIfExists "$env:ProgramFiles\nodejs"
    Add-PathIfExists "$env:LOCALAPPDATA\Programs\nodejs"
}

function Command-Exists($name) {
    return $null -ne (Get-Command $name -ErrorAction SilentlyContinue)
}

function Resolve-CommandPath {
    param([string[]]$Names)
    Refresh-NodePath
    foreach ($name in $Names) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command -and $command.Source) {
            return $command.Source
        }
    }
    return $null
}

function Resolve-NodeCommand {
    return Resolve-CommandPath @("node.exe", "node")
}

function Resolve-NpmCli {
    $nodeCmd = Resolve-NodeCommand
    if (-not $nodeCmd) {
        return $null
    }

    $nodeDir = Split-Path -Parent $nodeCmd
    $candidates = @(
        (Join-Path $nodeDir "node_modules\npm\bin\npm-cli.js"),
        (Join-Path (Split-Path -Parent $nodeDir) "node_modules\npm\bin\npm-cli.js")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }
    return $null
}

function Resolve-ElectronCli {
    $candidates = @(
        (Join-Path $electronDir "node_modules\electron\dist\electron.exe"),
        (Join-Path $electronDir "node_modules\electron\cli.js")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }
    return $null
}

function Require-Node {
    Refresh-NodePath
    if ((Command-Exists "node") -and (Resolve-NpmCli)) {
        return
    }

    $install = Ask-YesNo "A versao Electron precisa do Node.js LTS e do npm para abrir pelo codigo fonte.`n`nNao encontrei Node.js/npm neste computador.`n`nDeseja que eu instale automaticamente agora?"
    if (-not $install) {
        throw "Node.js nao instalado. Instale o Node.js LTS e abra novamente."
    }

    if (-not (Command-Exists "winget")) {
        Start-Process "https://nodejs.org/"
        throw "Nao encontrei o winget para instalar automaticamente. Abri o site do Node.js para instalar manualmente."
    }

    Write-Host "Instalando Node.js LTS pelo winget..."
    & winget install --id OpenJS.NodeJS.LTS -e --source winget --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        throw "A instalacao do Node.js pelo winget falhou."
    }

    Refresh-NodePath
    if (-not ((Command-Exists "node") -and (Resolve-NpmCli))) {
        Show-Info "Node.js foi instalado, mas o PATH ainda nao atualizou nesta sessao.`n`nFeche e abra este launcher novamente."
        exit 0
    }
}

function Ensure-ElectronDependencies {
    $electronCmd = Join-Path $electronDir "node_modules\.bin\electron.cmd"
    if (Test-Path -LiteralPath $electronCmd) {
        return
    }

    $install = Ask-YesNo "As dependencias da versao Electron ainda nao estao instaladas nesta pasta.`n`nDeseja instalar agora com npm install?"
    if (-not $install) {
        throw "Dependencias Electron nao instaladas."
    }

    Write-Host "Instalando dependencias Electron..."
    $nodeCmd = Resolve-NodeCommand
    $npmCli = Resolve-NpmCli
    if ((-not $nodeCmd) -or (-not $npmCli)) {
        throw "Encontrei o Node.js, mas nao consegui localizar os arquivos do npm."
    }
    Push-Location $electronDir
    try {
        & $nodeCmd $npmCli install
        if ($LASTEXITCODE -ne 0) {
            throw "npm install falhou."
        }
    } finally {
        Pop-Location
    }
}

function Source-Is-NewerThanBuild {
    $mainBuild = Join-Path $electronDir "dist\main\main.js"
    $rendererBuild = Join-Path $electronDir "dist\renderer\index.html"
    if (-not (Test-Path -LiteralPath $mainBuild) -or -not (Test-Path -LiteralPath $rendererBuild)) {
        return $true
    }

    $sourceFiles = @(
        Get-ChildItem -LiteralPath (Join-Path $electronDir "src") -Recurse -File
        Get-Item -LiteralPath (Join-Path $electronDir "package.json")
        Get-Item -LiteralPath (Join-Path $electronDir "vite.config.ts")
        Get-Item -LiteralPath (Join-Path $electronDir "tsconfig.json")
        Get-Item -LiteralPath (Join-Path $electronDir "tsconfig.main.json")
    )
    $newestSource = ($sourceFiles | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1).LastWriteTimeUtc
    $oldestBuild = (@((Get-Item -LiteralPath $mainBuild), (Get-Item -LiteralPath $rendererBuild)) | Sort-Object LastWriteTimeUtc | Select-Object -First 1).LastWriteTimeUtc
    return $newestSource -gt $oldestBuild
}

function Ensure-ElectronBuild {
    if (-not (Source-Is-NewerThanBuild)) {
        return
    }

    Write-Host "Preparando build local da versao Electron..."
    $nodeCmd = Resolve-NodeCommand
    $npmCli = Resolve-NpmCli
    if ((-not $nodeCmd) -or (-not $npmCli)) {
        throw "Encontrei o Node.js, mas nao consegui localizar os arquivos do npm."
    }
    Push-Location $electronDir
    try {
        & $nodeCmd $npmCli run build
        if ($LASTEXITCODE -ne 0) {
            throw "npm run build falhou."
        }
    } finally {
        Pop-Location
    }
}

try {
    if (-not (Test-Path -LiteralPath $electronDir)) {
        throw "Nao encontrei a pasta electron em:`n$electronDir"
    }

    Require-Node
    Ensure-ElectronDependencies
    Ensure-ElectronBuild

    $nodeCmd = Resolve-NodeCommand
    $electronCli = Resolve-ElectronCli
    if ((-not $nodeCmd) -or (-not $electronCli)) {
        throw "Nao consegui localizar os arquivos do Electron depois da instalacao."
    }

    if ([IO.Path]::GetExtension($electronCli).ToLowerInvariant() -eq ".exe") {
        Start-Process -FilePath $electronCli -ArgumentList "." -WorkingDirectory $electronDir
    } else {
        $stdoutLog = "$logFile.out"
        $stderrLog = "$logFile.err"
        Start-Process -FilePath $nodeCmd -ArgumentList @($electronCli, ".") -WorkingDirectory $electronDir -WindowStyle Hidden `
            -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog
    }
} catch {
    Show-Error $_.Exception.Message
    exit 1
}
