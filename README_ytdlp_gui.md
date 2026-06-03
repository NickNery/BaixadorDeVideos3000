# Gerenciador de Downloads Master em Python

Este pacote tem uma interface grafica em Python/Tkinter para baixar videos ou audios usando `yt-dlp`.

## Arquivos

- `ytdlp_gui_downloader.py`: aplicativo principal.
- `ytdlp_gui_config.json`: criado automaticamente quando voce salva preferencias.
- `TUTORIAL_DISTRIBUICAO_WINDOWS_MACOS.md`: guia para instalar em Windows/macOS e configurar atualizacoes.
- `Tutorial_BaixadorDeVideos3000.pdf`: versao em PDF formatada do tutorial de instalacao.
- `update_manifest_example.json`: modelo do arquivo online usado para atualizar todos os computadores.
- `argumentosExtras.txt`: lista de argumentos extras uteis do `yt-dlp` e exemplos de uso.

## Como usar

1. Instale Python 3 no Windows, se ainda nao tiver.
2. Baixe o `yt-dlp.exe`.
3. Coloque o `yt-dlp.exe` na mesma pasta do `ytdlp_gui_downloader.py`, ou selecione o executavel no campo `yt-dlp`.
4. Abra o app:

```powershell
python ytdlp_gui_downloader.py
```

Se o Windows usar o launcher `py`, tambem pode funcionar:

```powershell
py ytdlp_gui_downloader.py
```

Importante: os arquivos `Instalar_Dependencias_Windows.bat` e `Instalar_Dependencias_macOS.command` nao instalam o Python. Eles so instalam as bibliotecas depois que o Python ja esta instalado.

Para testar se o Python esta instalado no Windows:

```powershell
python --version
```

Para testar no macOS:

```zsh
python3 --version
```

## Biblioteca opcional para imagem de fundo

Para usar redimensionamento de imagem com qualidade, JPG, WEBP e os modos avancados de fundo, instale o Pillow:

```powershell
python -m pip install -r requirements.txt
```

Sem o Pillow, o app ainda abre, mas os recursos avancados de imagem ficam limitados.

## Instagram e Twitter/X

O app aceita links do YouTube, Instagram e Twitter/X porque quem faz a extracao e o `yt-dlp`.
Alguns links dessas plataformas podem exigir login. Nesses casos, selecione uma opcao em `Cookies / login`, como:

- `Usar cookies do Chrome`
- `Usar cookies do Edge`
- `Usar cookies do Firefox`
- `Usar arquivo cookies.txt`

Se usar cookies do navegador, deixe o navegador fechado caso o `yt-dlp` reclame que nao conseguiu ler os cookies.

## Audio MP3 e video MP4

Para converter audio em MP3 ou juntar video + audio em MP4 de alta qualidade, o `yt-dlp` normalmente precisa do `ffmpeg`.
Se aparecer erro relacionado a `ffmpeg`, baixe o `ffmpeg.exe` e deixe ele no PATH do Windows ou na mesma pasta do `yt-dlp.exe`.

No macOS, nao use `yt-dlp.exe`. Esse arquivo e apenas para Windows. Se aparecer `Errno 8` no Mac, normalmente significa que o sistema tentou abrir um `.exe`. Rode `Instalar_Dependencias_macOS.command` para instalar o `yt-dlp` correto para macOS.

## Erro de certificado SSL no macOS

Se aparecer `CERTIFICATE_VERIFY_FAILED`, `unable to get local issuer certificate` ou erro parecido, o Python do Mac nao esta encontrando certificados SSL confiaveis.

A partir da versao `1.3.0`, o app tenta usar automaticamente os certificados do pacote `certifi`. Para corrigir em computadores Mac, rode novamente:

```text
Instalar_Dependencias_macOS.command
```

Esse comando atualiza `yt-dlp` e instala/atualiza `certifi`.

## Personalizacao dentro do app

Abra a aba `Personalizar` dentro do proprio aplicativo para mudar:

- titulo do app;
- cor do fundo;
- cor dos paineis;
- cor dos textos;
- cor dos botoes;
- cores dos campos;
- imagem decorativa;
- modo da imagem: `none`, `banner` ou `full`;
- encaixe da imagem: `cover`, `contain`, `stretch` ou `original`;
- tamanho da imagem em porcentagem;
- altura da faixa quando usar `banner`;
- tamanho da fonte.

Depois clique em `Aplicar e salvar`.
Tambem existem botoes para remover a imagem e restaurar o visual padrao.
As preferencias ficam salvas no arquivo `ytdlp_gui_config.json`.

Observacao: no modo `full`, a imagem fica por tras da janela inteira. Os paineis continuam por cima para manter a leitura dos botoes e campos.

## Notificacoes e navegacao

O app usa dois botoes principais no topo:

- `Home`
- `Personalizar`

O botao da tela aberta fica maior automaticamente.
O botao `Home` apenas volta para a tela principal. Para baixar, use o botao `Iniciar download` dentro do painel.

Se a janela ficar pequena, as telas `Baixar` e `Personalizar` ganham rolagem vertical. Voce pode usar a barra lateral ou a roda do mouse.

As mensagens de andamento aparecem no status dentro da propria interface. O app nao usa mais pop-up azul para progresso.

Algumas mensagens finais aparecem como pop-ups no canto superior esquerdo da janela:

- verde para sucesso;
- vermelho para erro;

Quando um video esta baixando, o status dentro do painel mostra o retorno do `yt-dlp`. Quando terminar, aparece uma confirmacao verde. Se falhar, o app mostra um erro vermelho com as ultimas linhas retornadas pelo `yt-dlp`.

O modo `Video MP4` usa uma configuracao mais compativel: ele tenta baixar um MP4 pronto primeiro. Isso evita falhas em computadores sem `ffmpeg`. Para maxima qualidade com juncao de video + audio, instale o `ffmpeg`.

Se o `yt-dlp` ficar sem resposta por muito tempo, o app encerra a tentativa depois de um limite e mostra a causa mais provavel.

As fontes usadas na interface sao `Montserrat Regular` e `Montserrat Medium`. Se elas nao estiverem instaladas no Windows, o Tkinter usa uma fonte substituta automaticamente.

## Atualizacao do aplicativo

Na secao `yt-dlp`, existe o campo `URL de atualizacao do app`.

Cole nele a URL do seu `update_manifest.json` hospedado online e clique em `Verificar atualizacao`.
Quando houver uma versao nova, o app baixa os arquivos atualizados, substitui a versao antiga e reinicia.

Veja o passo a passo completo em:

```text
TUTORIAL_DISTRIBUICAO_WINDOWS_MACOS.md
```

Use apenas para baixar conteudos que voce tem permissao para salvar.
