# Tutorial de distribuicao - Windows e macOS

Este tutorial explica como instalar o Baixador YT-DLP em outros computadores Windows e Mac, e como preparar atualizacoes para todos os usuarios.

## 1. Arquivos que voce deve enviar

O pacote final fica em:

```text
release/Baixador_YTDLP_Windows_macOS.zip
```

Dentro dele, os arquivos principais ficam organizados assim:

- `src/ytdlp_gui_downloader.py`
- `requirements.txt`
- `scripts/Abrir_Baixador_YTDLP.bat`
- `scripts/Abrir_Baixador_YTDLP.command`
- `scripts/Instalar_Dependencias_Windows.bat`
- `scripts/Instalar_Dependencias_macOS.command`
- `README.md`
- `docs/update_manifest_example.json`
- `docs/argumentosExtras.txt`

Opcional no Windows:

- `yt-dlp.exe`

Se voce enviar `yt-dlp.exe` junto, o usuario Windows nao precisa instalar o yt-dlp por pip. Mesmo assim, ainda precisa do Python.

No macOS, o arquivo `yt-dlp.exe` nao deve ser executado. Ele e um executavel de Windows. O app no Mac usa o `yt-dlp` instalado pelas dependencias, ou roda `python3 -m yt_dlp`.

## 2. Instalacao no Windows

### Passo 1 - Instalar Python

O arquivo `Instalar_Dependencias_Windows.bat` nao instala o Python. Ele so instala as bibliotecas do programa depois que o Python ja existe no computador.

Se o computador ainda nao tiver Python instalado:

1. Baixe o Python em `https://www.python.org/downloads/windows/`.
2. Durante a instalacao, marque a opcao `Add python.exe to PATH`.
3. Conclua a instalacao.
4. Feche e abra novamente a pasta/terminal antes de continuar.

Para testar se deu certo, abra o Prompt de Comando ou PowerShell e rode:

```powershell
python --version
```

Se aparecer uma versao, por exemplo `Python 3.14.0`, pode continuar.

Se aparecer que `python` nao e reconhecido, reinstale o Python marcando `Add python.exe to PATH`.

### Passo 2 - Extrair o programa

1. Extraia o `.zip` do programa em uma pasta simples, por exemplo:

```text
C:\Baixador-YTDLP
```

Evite colocar dentro de pastas protegidas como `C:\Program Files`.

### Passo 3 - Instalar dependencias

1. Abra a pasta do programa.
2. Clique duas vezes em:

```text
scripts\Instalar_Dependencias_Windows.bat
```

Esse arquivo instala:

- `Pillow`, para imagem de fundo e redimensionamento;
- `yt-dlp`, caso voce nao esteja usando `yt-dlp.exe` na pasta.

Se esse arquivo abrir e fechar rapido, ou mostrar erro dizendo que `python` nao foi encontrado, volte ao Passo 1 e instale o Python corretamente.

### Passo 4 - Instalar ffmpeg

Para MP3 e MP4 em alta qualidade, instale o `ffmpeg`.

Opcoes:

- baixar o `ffmpeg.exe` e colocar na mesma pasta do programa;
- ou instalar pelo gerenciador de pacotes do Windows;
- ou adicionar o ffmpeg ao PATH do Windows.

### Passo 5 - Abrir o programa

Clique duas vezes em:

```text
scripts\Abrir_Baixador_YTDLP.bat
```

Para criar atalho:

1. Clique com o botao direito no `scripts\Abrir_Baixador_YTDLP.bat`.
2. Escolha `Enviar para > Area de trabalho (criar atalho)`.

## 3. Instalacao no macOS

### Passo 1 - Instalar Python

O arquivo `Instalar_Dependencias_macOS.command` nao instala o Python. Ele so instala as bibliotecas do programa depois que o Python ja existe no Mac.

Instale Python 3 pelo site:

```text
https://www.python.org/downloads/macos/
```

Ou pelo Homebrew:

```zsh
brew install python
```

Para testar se deu certo, abra o Terminal e rode:

```zsh
python3 --version
```

Se aparecer uma versao, por exemplo `Python 3.14.0`, pode continuar.

### Passo 2 - Instalar ffmpeg

No Mac, o jeito mais facil e pelo Homebrew:

```zsh
brew install ffmpeg
```

### Passo 3 - Extrair o programa

Extraia o `.zip` em uma pasta, por exemplo:

```text
/Users/SEU_USUARIO/Applications/Baixador-YTDLP
```

Ou:

```text
/Users/SEU_USUARIO/Desktop/Baixador-YTDLP
```

### Passo 4 - Liberar os arquivos `.command`

Abra o Terminal dentro da pasta do programa e rode:

```zsh
chmod +x scripts/Abrir_Baixador_YTDLP.command
chmod +x scripts/Instalar_Dependencias_macOS.command
```

### Passo 5 - Instalar dependencias

Clique duas vezes em:

```text
scripts/Instalar_Dependencias_macOS.command
```

Ou rode no Terminal:

```zsh
python3 -m pip install --upgrade -r requirements.txt
```

Esse passo instala tambem o `yt-dlp` para Mac. Se voce tentar usar o `yt-dlp.exe` no macOS, pode aparecer `Errno 8`, porque esse arquivo e de Windows.

Esse passo tambem instala/atualiza `certifi`, que fornece certificados SSL confiaveis para o Python. Se aparecer `CERTIFICATE_VERIFY_FAILED` ou `unable to get local issuer certificate`, rode `scripts/Instalar_Dependencias_macOS.command` novamente e depois abra o app de novo.

### Passo 6 - Abrir o programa

Clique duas vezes em:

```text
scripts/Abrir_Baixador_YTDLP.command
```

Se o macOS bloquear por seguranca:

1. Clique com o botao direito no arquivo.
2. Escolha `Abrir`.
3. Confirme que deseja abrir.

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
  "version": "1.2.0",
  "notes": "Resumo das mudancas desta versao.",
  "files": [
    {
      "path": "ytdlp_gui_downloader.py",
      "url": "https://SEU-SITE-OU-GITHUB/release/legacy/ytdlp_gui_downloader.py"
    },
    {
      "path": "src/ytdlp_gui_downloader.py",
      "url": "https://SEU-SITE-OU-GITHUB/src/ytdlp_gui_downloader.py"
    },
    {
      "path": "README.md",
      "url": "https://SEU-SITE-OU-GITHUB/README.md"
    },
    {
      "path": "requirements.txt",
      "url": "https://SEU-SITE-OU-GITHUB/requirements.txt"
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
2. Aumente a versao dentro do arquivo `src/ytdlp_gui_downloader.py`:

```python
APP_VERSION = "1.3.0"
```

3. Envie os arquivos novos para o seu GitHub/site.
4. Atualize o manifesto:

```json
"version": "1.3.0"
```

5. Atualize as URLs dos arquivos se necessario.
6. Nos computadores dos usuarios, abra o app e clique em:

```text
Verificar atualizacao
```

## 7. Como configurar a URL de atualizacao no app

Dentro do programa:

1. Abra a tela `Baixar`.
2. Procure a secao `yt-dlp`.
3. No campo `URL de atualizacao do app`, cole a URL do seu manifesto.
4. Clique em `Verificar atualizacao`.

O app salva essa URL no arquivo `ytdlp_gui_config.json`.

## 8. Importante sobre atualizacao automatica

O app esta preparado para buscar atualizacoes online, mas ele precisa de uma URL publica para o manifesto.

Sem essa URL, ele nao tem como saber onde buscar a nova versao.

Use sempre HTTPS e hospede apenas arquivos seus, porque o atualizador substitui arquivos do programa.
