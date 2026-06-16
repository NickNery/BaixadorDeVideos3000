# Tutorial de distribuicao - Windows e macOS

Este tutorial explica como instalar o Baixador YT-DLP em outros computadores Windows e Mac, e como preparar atualizacoes para todos os usuarios.

## 1. Arquivos que voce deve enviar

Para Windows, envie o instalador:

```text
release/BaixadorDeVideos3000_Setup_Windows.exe
```

Para macOS, envie o ZIP do instalador automatico:

```text
release/BaixadorDeVideos3000_Instalador_macOS.zip
```

O pacote de codigo fonte fica em:

```text
release/Baixador_YTDLP_Windows_macOS.zip
```

Dentro dele, os arquivos principais ficam organizados assim:

- `python/src/ytdlp_gui_downloader.py`
- `python/requirements.txt`
- `electron/`
- `BaixadorDeVideos3000_Electron.exe`
- `BaixadorDeVideos3000.vbs`
- `BaixadorDeVideos3000.command`
- `scripts/Abrir_Baixador_YTDLP.bat`
- `scripts/Abrir_Baixador_YTDLP.vbs`
- `scripts/Abrir_Baixador_YTDLP.command`
- `scripts/Instalar_Dependencias_Windows.bat`
- `scripts/Instalar_Dependencias_macOS.command`
- `scripts/Sincronizar_Release_Servidor_Windows.bat`
- `README.md`
- `docs/update_manifest_example.json`
- `docs/argumentosExtras.txt`

Opcional no Windows:

- `yt-dlp.exe`

Se voce enviar `yt-dlp.exe` junto, o usuario Windows nao precisa instalar o yt-dlp por pip. Mesmo assim, ainda precisa do Python.

No macOS, o arquivo `yt-dlp.exe` nao deve ser executado. Ele e um executavel de Windows. O app no Mac usa o `yt-dlp` instalado pelas dependencias, ou roda `python3 -m yt_dlp`.

## 2. Instalacao no Windows

### Passo 1 - Abrir o instalador

```text
BaixadorDeVideos3000_Setup_Windows.exe
```

Clique duas vezes nesse arquivo e aguarde.

### Passo 2 - O que ele instala

O instalador do Windows ja leva:

- aplicativo pronto;
- Python embutido no executavel;
- `yt-dlp.exe`;
- `ffmpeg.exe`;
- PDF de tutorial;
- icone na Area de Trabalho.

O usuario nao precisa entrar no site do Python e nao precisa instalar dependencias por fora.

### Passo 3 - Abrir o programa

Depois da instalacao, clique no atalho criado na Area de Trabalho:

```text
Baixador de Videos 3000
```

### Instalacao manual pelo codigo fonte

Use o pacote `Baixador_YTDLP_Windows_macOS.zip` apenas se voce quiser rodar pelo codigo fonte. Nesse caso, o usuario precisa instalar Python, dependencias e ffmpeg manualmente.

## 3. Instalacao no macOS

### Passo 1 - Extrair o instalador

Baixe e extraia o arquivo:

```text
BaixadorDeVideos3000_Instalador_macOS.zip
```

Coloque a pasta extraida em um lugar simples, por exemplo:

```text
/Users/SEU_USUARIO/Applications/Baixador-YTDLP
```

Ou:

```text
/Users/SEU_USUARIO/Desktop/Baixador-YTDLP
```

### Passo 2 - Abrir o instalador

Clique duas vezes em:

```text
Instalador_Automatico_macOS.command
```

Esse ZIP ja preserva a permissao de execucao do instalador. Se o macOS bloquear por seguranca:

1. Clique com o botao direito no instalador.
2. Escolha `Abrir`.
3. Confirme que deseja abrir.

### Passo 3 - Aguardar a instalacao

O instalador baixa automaticamente o que estiver faltando:

- Homebrew, se necessario;
- Python, se necessario;
- ffmpeg, se necessario;
- bibliotecas do app, incluindo `yt-dlp` e `certifi`.

Ele tambem cria um icone na Area de Trabalho chamado `Baixador de Videos 3000.app`.

Se aparecer uma janela ou mensagem do Homebrew, esta tudo certo. O Homebrew e usado para instalar Python, ffmpeg e componentes necessarios no Mac quando eles ainda nao estao prontos.

### Passo 4 - Abrir o programa

Depois da instalacao, clique no icone criado na Area de Trabalho.

Se aparecer `CERTIFICATE_VERIFY_FAILED` ou `unable to get local issuer certificate`, rode `scripts/Instalar_Dependencias_macOS.command` novamente e depois abra o app de novo.

Se aparecer um relatorio de crash do Python/Tkinter no macOS, rode novamente `Instalador_Automatico_macOS.command`. Ele recria o ambiente Python e ignora o Python 3.9 do Command Line Tools da Apple.

## 4. Como configurar atualizacao para todos os PCs

O programa agora tem um atualizador interno baseado em um arquivo online chamado manifesto.

A ideia e:

1. Voce hospeda os arquivos atualizados em algum lugar online.
2. Voce hospeda um `update_manifest.json`.
3. Todos os computadores configuram a mesma URL desse manifesto.
4. Quando voce publicar uma versao nova, qualquer usuario pode clicar em `Verificar atualizacao`.
5. O app baixa os arquivos novos, substitui os antigos e reinicia.

### Onde hospedar

Use um lugar com links diretos HTTPS, por exemplo:

- GitHub Releases;
- GitHub Pages;
- servidor proprio;
- storage publico com links diretos.

Evite links que abrem uma pagina HTML em vez de baixar o arquivo diretamente.

## 5. Exemplo de manifesto

Use o arquivo:

```text
docs/update_manifest_example.json
```

Modelo:

```json
{
  "version": "1.5.0",
  "notes": "Resumo das mudancas desta versao.",
  "files": [
    {
      "path": "ytdlp_gui_downloader.py",
      "url": "https://SEU-SITE-OU-GITHUB/release/legacy/ytdlp_gui_downloader.py"
    },
    {
      "path": "python/src/ytdlp_gui_downloader.py",
      "url": "https://SEU-SITE-OU-GITHUB/python/src/ytdlp_gui_downloader.py"
    },
    {
      "path": "README.md",
      "url": "https://SEU-SITE-OU-GITHUB/README.md"
    },
    {
      "path": "python/requirements.txt",
      "url": "https://SEU-SITE-OU-GITHUB/python/requirements.txt"
    }
  ]
}
```

### Campos

- `version`: versao mais nova disponivel.
- `notes`: texto mostrado para o usuario antes de atualizar.
- `files`: lista de arquivos que serao baixados.
- `path`: caminho onde o arquivo sera salvo dentro da pasta do app.
- `url`: link direto para baixar o arquivo novo.

## 6. Como publicar uma nova atualizacao

Sempre que voce quiser atualizar todos os computadores:

1. Edite o programa.
2. Aumente a versao dentro do arquivo `python/src/ytdlp_gui_downloader.py` e no `electron/package.json`:

```python
APP_VERSION = "1.5.3"
```

3. Envie os arquivos novos para o seu GitHub/site.
4. Atualize o manifesto:

```json
"version": "1.5.3"
```

5. Atualize as URLs dos arquivos se necessario.
6. Sincronize a pasta compartilhada do servidor.
7. Nos computadores dos usuarios, abra o app e clique em:

```text
Verificar atualizacao
```

Regra importante: quando a mudanca for uma regra do programa, aplique na versao Python e na versao Electron. Quando for somente visual e depender de React/CSS, ela pode ficar apenas na versao Electron.

Para abrir a versao Electron no Windows, use:

```text
BaixadorDeVideos3000_Electron.exe
```

Esse arquivo entra na pasta `electron/` automaticamente, verifica Node.js/npm, pergunta se pode instalar quando faltar, roda `npm install` e abre o app.

## 7. Como sincronizar a pasta do servidor

Quando houver uma nova versao, alem de atualizar o computador local e o GitHub, copie a versao nova para:

```text
Z:\AUDIO VISUAL\ELEMENTOS DE EDIÃ‡ÃƒO\BaixadorDeVideos3000
```

No Windows, execute:

```text
scripts\Sincronizar_Release_Servidor_Windows.bat
```

Esse script cria a pasta do servidor, se ela ainda nao existir, e copia `python`, `electron`, `docs`, `scripts`, `release`, `assets`, `README.md` e `update_manifest.json`.

## 8. Como configurar a URL de atualizacao no app

Dentro do programa:

1. Abra a tela `Baixar`.
2. Procure a secao `yt-dlp`.
3. No campo `URL de atualizacao do app`, cole a URL do seu manifesto.
4. Clique em `Verificar atualizacao`.

O app salva essa URL no arquivo `ytdlp_gui_config.json`.

## 9. Importante sobre atualizacao automatica

O app esta preparado para buscar atualizacoes online, mas ele precisa de uma URL publica para o manifesto.

Sem essa URL, ele nao tem como saber onde buscar a nova versao.

Use sempre HTTPS e hospede apenas arquivos seus, porque o atualizador substitui arquivos do programa.
