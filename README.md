# BaixadorDeVideos3000

Aplicativo em Python/Tkinter para baixar videos e audios com `yt-dlp`, usando o visual Edge Solutions.

## Estrutura

- `src/`: codigo fonte do aplicativo.
- `docs/`: tutoriais, PDF, argumentos extras e exemplos de manifesto.
- `scripts/`: atalhos e instaladores para Windows/macOS.
- `release/`: arquivos de distribuicao, incluindo o ZIP final.
- `requirements.txt`: dependencias Python.
- `update_manifest.json`: manifesto publico usado pelo atualizador do app.

Existe apenas este `README.md` na raiz do projeto.

## Download rapido

No Windows, o jeito mais simples e baixar e abrir o instalador:

```text
release/BaixadorDeVideos3000_Setup_Windows.exe
```

Esse instalador ja leva o aplicativo, Python embutido no executavel, `yt-dlp.exe` e `ffmpeg.exe`. A pessoa nao precisa entrar no site do Python.

No macOS, enquanto o `.dmg` final nao for gerado em um Mac, use o instalador automatico:

```text
scripts/Instalador_Automatico_macOS.command
```

Ele instala Python, ffmpeg e dependencias automaticamente quando estiverem faltando.

Tambem existe o pacote final em ZIP:

```text
release/Baixador_YTDLP_Windows_macOS.zip
```

Dentro do ZIP:

1. Rode `scripts/Instalar_Dependencias_Windows.bat` no Windows ou `scripts/Instalar_Dependencias_macOS.command` no macOS.
2. Abra com `scripts/Abrir_Baixador_YTDLP.bat` no Windows ou `scripts/Abrir_Baixador_YTDLP.command` no macOS.

## Gerar instaladores

Windows:

```powershell
scripts\Build_Instalador_Windows.ps1
```

macOS:

```zsh
scripts/Build_Instalador_macOS.command
```

Observacao: o `.dmg` do macOS precisa ser gerado em um Mac. O Windows nao consegue compilar um aplicativo macOS nativo.

## Rodar pelo codigo fonte

Na raiz do projeto:

```powershell
python src/ytdlp_gui_downloader.py
```

No macOS:

```zsh
python3 src/ytdlp_gui_downloader.py
```

## Atualizacao do app

Use esta URL no campo `URL de atualizacao do app`:

```text
https://raw.githubusercontent.com/NickNery/BaixadorDeVideos3000/main/update_manifest.json
```

O manifesto baixa os arquivos dos novos caminhos (`src/`, `docs/`, `scripts/`) e tambem instala um launcher legado na raiz para nao quebrar atalhos antigos.

## Sincronizar com a pasta do servidor

Depois de gerar uma nova versao, sincronize tambem a pasta compartilhada:

```text
Z:\AUDIO VISUAL\ELEMENTOS DE EDIÇÃO\BaixadorDeVideos3000
```

No Windows, use:

```text
scripts/Sincronizar_Release_Servidor_Windows.bat
```

Esse script cria a pasta no servidor, se ela ainda nao existir, e copia `src`, `docs`, `scripts`, `release`, `README.md`, `requirements.txt` e `update_manifest.json`.

## Documentacao

- Tutorial Windows/macOS: `docs/TUTORIAL_DISTRIBUICAO_WINDOWS_MACOS.md`
- Tutorial em PDF: `docs/Tutorial_BaixadorDeVideos3000.pdf`
- Argumentos extras do `yt-dlp`: `docs/argumentosExtras.txt`
- Exemplo de manifesto: `docs/update_manifest_example.json`

## macOS

No macOS, nao use `yt-dlp.exe`; ele e apenas para Windows. Rode `scripts/Instalar_Dependencias_macOS.command` antes de abrir o app.

Se aparecer `CERTIFICATE_VERIFY_FAILED` ou `unable to get local issuer certificate`, rode `scripts/Instalar_Dependencias_macOS.command` novamente para atualizar `yt-dlp` e `certifi`.

Use apenas para baixar conteudos que voce tem permissao para salvar.
