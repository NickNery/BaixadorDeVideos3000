# BaixadorDeVideos3000

Aplicativo para baixar videos e audios com `yt-dlp`, usando o visual Edge Solutions.

O projeto tem duas versoes mantidas em paralelo:

- `Bin/python/`: versao Python/Tkinter.
- `Bin/electron/`: versao TypeScript + React + Electron.

## Estrutura

- `Bin/`: codigo fonte, assets, docs, releases e launchers usados no desenvolvimento.
- `Bin/launcher/`: atalhos para abrir a versao Python e a versao Electron.
- `Bin/scripts/`: scripts de build, instalacao auxiliar e sincronizacao.
- `Bin/release/`: arquivos de distribuicao e executaveis gerados.
- `Win/`: pacote separado para Windows, com `Win/setup/` e `Win/Bin/`.
- `Mac/`: pacote separado para macOS, com `Mac/setup/` e `Mac/Bin/`.
- `setup/`: fontes dos instaladores principais usados para gerar/copiar os pacotes.
- `update_manifest.json`: manifesto publico usado pelo atualizador do app.

## Setup Recomendado

Windows:

```text
Win/setup/Setup_BaixadorDeVideos3000_Windows.exe
```

macOS:

```text
Mac/setup/Setup_BaixadorDeVideos3000_macOS.command
```

Os setups preparam as dependencias necessarias e perguntam quais atalhos criar na area de trabalho: Python, Electron ou ambos.

Para remover ZIPs repetidos, logs, temporarios e runtimes antigos no macOS sem apagar a instalacao atual:

```text
Mac/setup/Limpar_BaixadorDeVideos3000_macOS.command
```

## Abrir Sem Setup

Python:

```text
Bin/launcher/BaixadorDeVideos3000.vbs
Bin/launcher/BaixadorDeVideos3000.command
```

Electron:

```text
Bin/launcher/BaixadorDeVideos3000_Electron.exe
Bin/launcher/BaixadorDeVideos3000_Electron.command
```

No Windows e no macOS, se o Electron nao abrir, rode primeiro o setup do sistema correspondente. Ele instala uma copia local do app e baixa o runtime oficial do Electron sem depender de Node.js/npm no computador do usuario final.

## Desenvolvimento

Python:

```powershell
python Bin/python/src/ytdlp_gui_downloader.py
```

Electron:

```powershell
cd Bin/electron
npm install
npm run build
```

## Gerar Instaladores

Windows:

```powershell
Bin\scripts\Build_Instalador_Windows.ps1
```

macOS:

```zsh
Bin/scripts/Build_Instalador_macOS.command
```

O `.dmg` do macOS precisa ser gerado em um Mac.

## Atualizacao

Use esta URL no campo `URL de atualizacao do app`:

```text
https://raw.githubusercontent.com/NickNery/BaixadorDeVideos3000/main/update_manifest.json
```

A partir da versao `1.6.0`, o manifesto usa caminhos `Bin/...`. O app novo evita criar `Bin/Bin` quando ja estiver rodando de dentro da pasta `Bin`.

## Sincronizar Servidor

No Windows:

```text
Bin\scripts\Sincronizar_Release_Servidor_Windows.bat
```

Esse script prepara `Win/` e `Mac/` e copia a distribuicao separada para:

```text
Z:\AUDIO VISUAL\ELEMENTOS DE EDICAO\BaixadorDeVideos3000
```

## Manutencao

Mudancas de comportamento devem ser aplicadas nas duas versoes:

- Python: `Bin/python/src/ytdlp_gui_downloader.py`
- Electron: `Bin/electron/src/main/main.ts` e `Bin/electron/src/renderer/App.tsx`

Mudancas apenas visuais podem ficar somente na versao Electron quando usarem React/CSS.

Use apenas para baixar conteudos que voce tem permissao para salvar.
