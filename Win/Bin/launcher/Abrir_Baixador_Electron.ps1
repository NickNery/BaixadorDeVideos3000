$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Windows.Forms

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$electronDir = Join-Path $root "electron"
$logFile = Join-Path $root "BaixadorDeVideos3000_Electron.log"
$safeWorkingDir = $env:TEMP
if (-not $safeWorkingDir) {
    $safeWorkingDir = $env:USERPROFILE
}
if (-not $safeWorkingDir) {
    $safeWorkingDir = $env:SystemRoot
}
$compiledLauncher = Join-Path $root "launcher\BaixadorDeVideos3000_Electron.exe"
if (Test-Path -LiteralPath $compiledLauncher) {
    Start-Process -FilePath $compiledLauncher -WorkingDirectory $safeWorkingDir
    exit 0
}

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

function Get-ElectronPackageVersion {
    $packageFile = Join-Path $electronDir "node_modules\electron\package.json"
    if (Test-Path -LiteralPath $packageFile) {
        try {
            return ((Get-Content -LiteralPath $packageFile -Raw) | ConvertFrom-Json).version
        } catch {
            return "runtime"
        }
    }
    return "runtime"
}

function Prepare-LocalElectronExe {
    $sourceDist = Join-Path $electronDir "node_modules\electron\dist"
    $sourceExe = Join-Path $sourceDist "electron.exe"
    if (-not (Test-Path -LiteralPath $sourceExe)) {
        return $null
    }

    $base = $env:LOCALAPPDATA
    if (-not $base) {
        $base = $env:TEMP
    }
    if (-not $base) {
        $base = $env:USERPROFILE
    }

    $targetDist = Join-Path $base ("BaixadorDeVideos3000\ElectronRuntime\" + (Get-ElectronPackageVersion))
    $targetExe = Join-Path $targetDist "electron.exe"

    $needsCopy = $true
    if (Test-Path -LiteralPath $targetExe) {
        $needsCopy = (Get-Item -LiteralPath $targetExe).Length -ne (Get-Item -LiteralPath $sourceExe).Length
    }

    if ($needsCopy) {
        New-Item -ItemType Directory -Force -Path $targetDist | Out-Null
        robocopy $sourceDist $targetDist /E /R:2 /W:2 /NFL /NDL /NJH /NJS | Out-Null
        if ($LASTEXITCODE -ge 8) {
            throw "Nao consegui preparar o runtime local do Electron."
        }
    }

    return $targetExe
}

function Test-ElectronRuntimeReady {
    $electronExe = Join-Path $electronDir "node_modules\electron\dist\electron.exe"
    return Test-Path -LiteralPath $electronExe
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
    if (Test-ElectronRuntimeReady) {
        return
    }

    $nodeModules = Join-Path $electronDir "node_modules"
    if (Test-Path -LiteralPath $nodeModules) {
        $install = Ask-YesNo "A instalacao do Electron parece incompleta nesta pasta.`n`nDeseja reparar agora com npm install?"
    } else {
        $install = Ask-YesNo "As dependencias da versao Electron ainda nao estao instaladas nesta pasta.`n`nDeseja instalar agora com npm install?"
    }
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
        $installJs = Join-Path $electronDir "node_modules\electron\install.js"
        if ((-not (Test-ElectronRuntimeReady)) -and (Test-Path -LiteralPath $installJs)) {
            & $nodeCmd $installJs
            if ($LASTEXITCODE -ne 0) {
                throw "Reparo do Electron falhou."
            }
        }
    } finally {
        Pop-Location
    }

    if (-not (Test-ElectronRuntimeReady)) {
        throw "As dependencias foram instaladas, mas o electron.exe nao apareceu.`n`nIsso normalmente acontece quando o download do Electron foi bloqueado ou interrompido.`n`nConfira os logs na pasta do aplicativo."
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

    $localElectronExe = Prepare-LocalElectronExe
    if ($localElectronExe) {
        $electronCli = $localElectronExe
    }

    if ([IO.Path]::GetExtension($electronCli).ToLowerInvariant() -eq ".exe") {
        $electronArgs = ('--disable-gpu "{0}"' -f $electronDir)
        $stdoutLog = "$logFile.out"
        $stderrLog = "$logFile.err"
        $process = Start-Process -FilePath $electronCli -ArgumentList $electronArgs -WorkingDirectory $safeWorkingDir `
            -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog -PassThru
        Start-Sleep -Seconds 3
        if ($process.HasExited -and $process.ExitCode -ne 0) {
            $details = ""
            if (Test-Path -LiteralPath $stderrLog) {
                $details = Get-Content -LiteralPath $stderrLog -Raw
            }
            throw "O Electron tentou abrir, mas fechou logo em seguida.`n`nLog:`n$stderrLog`n`n$details"
        }
    } else {
        $stdoutLog = "$logFile.out"
        $stderrLog = "$logFile.err"
        $nodeArgs = ('"{0}" --disable-gpu "{1}"' -f $electronCli, $electronDir)
        $process = Start-Process -FilePath $nodeCmd -ArgumentList $nodeArgs -WorkingDirectory $safeWorkingDir -WindowStyle Hidden `
            -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog -PassThru
        Start-Sleep -Seconds 3
        if ($process.HasExited -and $process.ExitCode -ne 0) {
            $details = ""
            if (Test-Path -LiteralPath $stderrLog) {
                $details = Get-Content -LiteralPath $stderrLog -Raw
            }
            throw "O Electron tentou abrir, mas fechou logo em seguida.`n`nLog:`n$stderrLog`n`n$details"
        }
    }
} catch {
    Show-Error $_.Exception.Message
    exit 1
}
