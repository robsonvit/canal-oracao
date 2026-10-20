# ✅ Deu Certo — Automação Canal Oração com Aprovação no Telegram, Legendas e Thumbnail Impact

**Data:** 20/10/2026 às 19:44
**Projeto:** Canal Oração (JESUS VIVE / VIDEOS JESUS)

---

## O que funcionou

O pipeline de geração automatizada de vídeos diários de oração cristã alcançou o estado de produção perfeito, com fluxo 100% testado e validado no GitHub Actions. Em vez de publicar automaticamente no YouTube, o sistema agora envia todos os materiais produzidos (thumbnail de alto clique, título formatado com dia da semana, descrição pastoral rica em SEO e vídeo renderizado em 1080p compactado para visualização) diretamente para o canal/bot do Telegram para avaliação e aprovação humana prévia. O erro 413 do Whisper foi resolvido através de compressão de áudio antes da transcrição, as legendas foram restauradas para o centro absoluto da tela com `Alignment=10`, e as thumbnails são geradas usando imagem sacra do Pinterest e tipografia pesada na fonte IMPACT.

---

## Arquivos envolvidos

| Arquivo | Papel na solução |
|---|---|
| `scripts/pipeline.py` | Orquestrador principal com 6 etapas, protegendo título base e chamando envio para aprovação no Telegram |
| `scripts/enviar_telegram.py` | Envia thumbnail (foto), descrição completa e vídeo compactado (<35 MB) via API do Telegram Bot |
| `scripts/gerar_oracao.py` | Gera texto pastoral com Groq AI e descrição estruturada com dupla camada anti-vazamento de prompt |
| `scripts/gerar_audio.py` | Gera áudio com Kokoro TTS, comprime para MP3 16kHz mono (48k) e transcreve 300+ blocos SRT via Whisper |
| `scripts/gerar_capa.py` | Busca arte sacra 16:9 no Pinterest, aplica degradê preto e tipografia em amarelo/branco na fonte IMPACT |
| `scripts/montar_video.py` | Concatena clipes Pexels sem repetições consecutivas e queima legendas no centro (`Alignment=10`) com música de fundo |
| `scripts/pesquisar_titulo.py` | Pesquisa concorrentes no YouTube e gera título otimizado garantindo Salmo, tema e dia da semana |
| `scripts/upload_youtube.py` | Módulo de upload via OAuth 2.0 (preservado para quando o usuário aprovar publicação definitiva) |
| `scripts/baixar_musica.py` | Baixa e faz cache local da trilha sonora instrumental solene |
| `scripts/buscar_video.py` | Busca clipes cinematográficos no Pexels filtrando vídeos usados recentemente |
| `assets/fonts/impact.ttf` | Fonte tipográfica Impact empacotada no repositório para renderização consistente no Linux |
| `.github/workflows/main.yml` | Workflow GitHub Actions com runners Ubuntu, FFmpeg, fontes e secrets do Telegram e YouTube |
| `requirements.txt` | Dependências Python do projeto (Groq, Pillow, kokoro, soundfile, requests, etc.) |

---

## Como replicar

1. **Dependências do Ambiente:**
   - Instalar Python 3.11+ e FFmpeg com suporte a `libass`.
   - Empacotar a fonte `assets/fonts/impact.ttf` no repositório para evitar divergência de fontes entre SOs.

2. **Áudio e Legendas sem Erro de Payload:**
   - Kokoro gera WAV de 24kHz. Se o áudio tiver mais de 6 minutos, o WAV excede os 25 MB do Groq Whisper.
   - Sempre converter para MP3 mono 16kHz a 48kbps antes de enviar para o endpoint de transcrição.
   - Usar `Alignment=10` no filtro `subtitles` do FFmpeg para posicionar as legendas no centro da tela (padrão SSA v4).

3. **Geração de Thumbnail com Alta Taxa de Clique:**
   - Buscar no Pinterest termos específicos: `"holy bible church altar wallpaper hd 16:9"` ou `"Jesus Cristo salvador pintura hd 16:9"`.
   - Gerar canvas 1280x720, aplicar degradê escuro à esquerda e renderizar 3 linhas de texto em IMPACT (Branco, Branco, Amarelo) com contorno preto pesado (`stroke_w`).

4. **Envio para o Telegram:**
   - Se o vídeo final em 1080p for maior que 48 MB, comprimir uma versão de visualização usando:
     `ffmpeg -y -i video.mp4 -vf scale=640:-2 -c:v libx264 -b:v 600k -maxrate 700k -bufsize 1200k -preset veryfast -c:a aac -b:a 64k preview.mp4`
   - O arquivo fica em torno de 30 a 35 MB, sendo aceito instantaneamente pela API de bots do Telegram.

---

## Observações

- **Limites da API do YouTube:** O YouTube impõe um limite diário de envios por canal (`uploadLimitExceeded` / HTTP 400 ou 429). O fluxo de aprovação prévia no Telegram evita consumir a cota desnecessariamente durante os testes.
- **Evitar UnboundLocalError:** Nunca importar módulos como `import re` dentro de funções se eles forem utilizados em condicionais anteriores; manter sempre as importações na raiz do arquivo.
- **Anti-vazamento de prompts:** Nunca colocar exemplos de instruções complexas dentro do valor JSON do prompt do LLM; usar geradores determinísticos em Python para descrições fixas e sanitizar termos de prompt.
