# BaixadorDeVideos3000

Aplicativo para baixar videos e audios com `yt-dlp`, usando o visual Edge Solutions.

O projeto agora tem duas versoes mantidas em paralelo:

- `python/`: versao estavel em Python/Tkinter.
- `electron/`: nova versao em TypeScript + React + Electron.

## Estrutura

- `python/`: codigo fonte e dependencias da versao Python.
- `electron/`: codigo fonte da nova versao Electron/React.
- `docs/`: tutoriais, PDF, argumentos extras e exemplos de manifesto.
- `scripts/`: atalhos e instaladores para Windows/macOS.
- `release/`: arquivos de distribuicao, incluindo o ZIP final.
- `assets/`: imagens e icones do aplicativo.
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
release/BaixadorDeVideos3000_Instalador_macOS.zip
```

Extraia o ZIP inteiro e clique duas vezes em `Instalador_Automatico_macOS.command`. O ZIP preserva a permissao de execucao do arquivo, evitando o erro de acesso do macOS. Ele instala Python, ffmpeg e dependencias automaticamente quando estiverem faltando, cria um icone na Area de Trabalho e abre o app.

Se o macOS bloquear por seguranca, clique com o botao direito no instalador, escolha `Abrir` e confirme.

Se aparecer uma instalacao do Homebrew durante esse processo, isso e normal. O instalador usa o Homebrew para instalar Python, ffmpeg e componentes necessarios quando o Mac ainda nao tem uma versao compativel. O Python 3.9 do Command Line Tools da Apple e ignorado porque pode travar o Tkinter em Macs novos.

Tambem existe o pacote final em ZIP:

```text
release/Baixador_YTDLP_Windows_macOS.zip
```

Dentro do ZIP:

1. Rode `scripts/Instalar_Dependencias_Windows.bat` no Windows ou `scripts/Instalar_Dependencias_macOS.command` no macOS.
2. Abra pela raiz da pasta com `BaixadorDeVideos3000.vbs` no Windows ou `BaixadorDeVideos3000.command` no macOS.
3. Para abrir a nova versao Electron no Windows, use `BaixadorDeVideos3000_Electron.exe`.

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
python python/src/ytdlp_gui_downloader.py
```

No macOS:

```zsh
python3 python/src/ytdlp_gui_downloader.py
```

## Rodar a versao Electron

No Windows, use o launcher facil da raiz:

```text
BaixadorDeVideos3000_Electron.exe
```

Ele entra na pasta `electron/` automaticamente. Se Node.js/npm ou as dependencias Electron estiverem faltando, ele pergunta se pode instalar para voce.

No macOS, use:

```text
BaixadorDeVideos3000_Electron.command
```

Para rodar manualmente, instale o Node.js LTS e entre na pasta Electron:

```powershell
cd electron
npm install
```

Em desenvolvimento, rode o renderer e o Electron:

```powershell
npm run dev:renderer
npm run dev:electron
```

## Atualizacao do app

Use esta URL no campo `URL de atualizacao do app`:

```text
https://raw.githubusercontent.com/NickNery/BaixadorDeVideos3000/main/update_manifest.json
```

O manifesto baixa os arquivos dos caminhos `python/`, `electron/`, `docs/` e `scripts/`, alem dos launchers da raiz.

## Sincronizar com a pasta do servidor

Depois de gerar uma nova versao, sincronize tambem a pasta compartilhada:

```text
Z:\AUDIO VISUAL\ELEMENTOS DE EDIÇÃO\BaixadorDeVideos3000
```

No Windows, use:

```text
scripts/Sincronizar_Release_Servidor_Windows.bat
```

Esse script cria a pasta no servidor, se ela ainda nao existir, e copia `python`, `electron`, `docs`, `scripts`, `release`, `assets`, `README.md` e `update_manifest.json`.

## Regra de manutencao

Toda mudanca de comportamento do programa deve ser aplicada nas duas versoes:

- Python: `python/src/ytdlp_gui_downloader.py`
- Electron: `electron/src/main/main.ts` e `electron/src/renderer/App.tsx`

Mudancas apenas visuais podem ficar somente na versao Electron quando usarem React/CSS.

## Documentacao

- Tutorial Windows/macOS: `docs/TUTORIAL_DISTRIBUICAO_WINDOWS_MACOS.md`
- Tutorial em PDF: `docs/Tutorial_BaixadorDeVideos3000.pdf`
- Argumentos extras do `yt-dlp`: `docs/argumentosExtras.txt`
- Exemplo de manifesto: `docs/update_manifest_example.json`

## macOS

No macOS, nao use `yt-dlp.exe`; ele e apenas para Windows. Rode `scripts/Instalar_Dependencias_macOS.command` antes de abrir o app.

Se aparecer `CERTIFICATE_VERIFY_FAILED` ou `unable to get local issuer certificate`, rode `scripts/Instalar_Dependencias_macOS.command` novamente para atualizar `yt-dlp` e `certifi`.

Se o app fechar com um relatorio de crash do Python/Tkinter no macOS, rode novamente `release/BaixadorDeVideos3000_Instalador_macOS.zip`. Ele remove a `.venv` antiga e cria uma nova com um Python compativel.

Use apenas para baixar conteudos que voce tem permissao para salvar.
