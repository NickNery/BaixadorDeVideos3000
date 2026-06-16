# Versao Electron

Esta pasta contem a nova versao do BaixadorDeVideos3000 em TypeScript + React + Electron.

## Instalar dependencias

No Windows, o jeito mais simples e abrir pela raiz do projeto:

```text
BaixadorDeVideos3000_Electron.exe
```

Esse launcher verifica Node.js/npm, pergunta se pode instalar quando faltar, roda `npm install` e abre a versao Electron.

No macOS, use o arquivo da raiz:

```text
BaixadorDeVideos3000_Electron.command
```

Manual:

Instale o Node.js LTS e rode:

```bash
npm install
```

## Rodar em desenvolvimento

Terminal 1:

```bash
npm run dev:renderer
```

Terminal 2:

```bash
npm run dev:electron
```

## Build

```bash
npm run build
```

## Empacotar

Windows:

```bash
npm run package:win
```

macOS:

```bash
npm run package:mac
```

## Manutencao em paralelo

Quando uma regra do aplicativo mudar, aplique a mesma regra em:

- `../python/src/ytdlp_gui_downloader.py`
- `src/main/main.ts`
- `src/renderer/App.tsx`

O React/Electron deve ser a versao principal para evolucao visual. O Python fica como versao estavel/legada.
