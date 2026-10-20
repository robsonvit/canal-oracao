# 🙏 Canal Oração — Arquitetura, Ferramentas e Estado Atual do Projeto

Documento de referência técnica detalhado contendo o estado atual, mapeamento de componentes, ferramentas utilizadas e o fluxo passo a passo de automação do canal.

---

## 1. 📌 Estado Atual do Projeto

- **Status Geral:** **100% Funcional e em Produção**.
- **Ambientes Suportados:** Execução local e automação em nuvem via **GitHub Actions**.
- **Histórico e Estabilidade:** O sistema possui mais de 270 vídeos processados com rastreamento no arquivo `data/videos_usados.json` para evitar repetições.
- **Validações Registradas:** Possui marcos de sucesso salvos em:
  - `deu certo - automacao-canal-oracao-youtube/RESUMO.md` (validação inicial do pipeline e upload).
  - `deu certo - versao-antes-melhorias-titulo-agendamento/RESUMO.md` (validação das otimizações de SEO e agendamento).
- **Branch Principal:** `master` sincronizada com o repositório remoto.

---

## 2. 🛠️ Ferramentas e Tecnologias Integradas

| Ferramenta / Tecnologia | Versão / Modelo | Função Principal no Sistema |
| :--- | :--- | :--- |
| **Groq AI** | `llama-3.3-70b-versatile` | Geração do roteiro da oração (~2.500 palavras), descrição otimizada para SEO e reescrita de títulos baseada em concorrentes. |
| **Kokoro TTS** | `kokoro >= 0.9.4` (Voz `pm_santa`) | Síntese de voz grave masculina em Português do Brasil com entonação solene e natural. |
| **Groq Whisper** | `whisper-large-v3-turbo` | Transcrição ultra-precisa do áudio gerado para criar legendas `.srt` com marcação temporal palavra a palavra. |
| **Pexels API** | REST API v1 | Busca e download automatizado de filmagens de natureza em alta definição para o plano de fundo. |
| **Wikimedia Commons & Bing Search** | Web APIs / Scraper seguro | Coleta de arte sacra de alta definição e domínio público com filtro `safeSearch=Strict` para a capa do vídeo. |
| **Pillow (PIL)** | `>= 10.0.0` | Criação e renderização da thumbnail (1280×720) com texto em degradê, contornos (`stroke`) e tipografia de alto impacto. |
| **FFmpeg & ffprobe** | CLI | Processamento de vídeo (corte, espelhamento, desaceleração, remoção de metadados), sincronização de legendas e mixagem com música instrumental. |
| **Google APIs / YouTube Data API** | `v3` | Pesquisa de termos e estatísticas de vídeos concorrentes, upload do arquivo `.mp4`, agendamento de publicação e envio da thumbnail. |
| **GitHub Actions** | Workflow CI/CD | Orquestração da execução na nuvem, com instalação de dependências, controle de segredos e commit de dados de histórico. |

---

## 3. 📁 Mapeamento de Arquivos e Scripts

```
CANAL ORAÇÃO/
├── .github/
│   └── workflows/
│       └── main.yml                  # Configuração do GitHub Actions para execução remota
├── data/
│   ├── bg_music.mp3                  # Trilha sonora instrumental de piano de fundo
│   └── videos_usados.json            # Base de dados de vídeos já usados e datas de uso
├── output/                           # Diretório de geração de artefatos temporários e finais
│   ├── audio.wav                     # Áudio gerado pela locução do Kokoro
│   ├── legendas.srt                  # Arquivo de legendas com timestamps sincronizados
│   ├── oracao.json                   # Metadados da oração (título, descrição, tags, salmo)
│   ├── thumbnail.jpg                 # Capa do vídeo gerada em 1280x720
│   └── video_final.mp4 (renomeado)   # Vídeo final montado em 1080p pronto para o YouTube
├── scripts/
│   ├── pipeline.py                   # Orquestrador principal de todos os 6 passos
│   ├── gerar_oracao.py               # Redação da oração pastoral via Groq LLM
│   ├── pesquisar_titulo.py           # Análise de concorrentes no YouTube e geração de título SEO
│   ├── gerar_audio.py                # Síntese de voz com Kokoro TTS + legendas com Groq Whisper
│   ├── buscar_video.py               # Busca no Pexels e transformações anti-reúso
│   ├── gerar_capa.py                 # Criação da thumbnail personalizada com Pillow
│   ├── montar_video.py               # Renderização do vídeo final e mixagem via FFmpeg
│   ├── baixar_musica.py              # Download da trilha instrumental suave (Archive.org)
│   ├── upload_youtube.py             # Envio, agendamento de publicação e thumbnail via OAuth 2.0
│   └── obter_refresh_token.py        # Utilitário local para autenticação inicial do canal
├── requirements.txt                  # Lista de dependências Python
└── ESTADO_DO_PROJETO.md              # Este documento de referência técnica
```

---

## 4. 🔄 Fluxo de Execução do Pipeline (`scripts/pipeline.py`)

A automação executa as seguintes etapas de forma encadeada:

```
[ PASSO 1 ] Geração da Oração & Pesquisa de Título
      │     • Seleciona o salmo do dia de forma rotativa por dia do ano
      │     • Groq LLM gera ~2.500 palavras no estilo pastoral (estilo Bispo Bruno Leonardo)
      │     • Busca os 3 vídeos mais vistos no YouTube para o tema
      │     • Gera título 90% similar aos de maior sucesso e extrai tags relevantes (max 500 chars)
      ▼
[ PASSO 2 ] Síntese de Voz & Legendas
      │     • Kokoro TTS gera o áudio WAV com voz grave masculina (pm_santa)
      │     • Groq Whisper transcreve o áudio e gera o arquivo SRT segmentado a cada 5 palavras
      ▼
[ PASSO 3 ] Curadoria e Tratamento de Clipes
      │     • Busca 12 clipes no Pexels ignorando vídeos usados nos últimos 5 dias
      │     • Aplica corte de 5s, espelhamento horizontal (hflip) e desaceleração para 0.8x
      │     • Remove todos os metadados dos clipes brutos
      ▼
[ PASSO 4 ] Geração da Capa (Thumbnail)
      │     • Busca imagem sacra segura no Wikimedia Commons ou Bing (SafeSearch Strict)
      │     • Aplica fusão em degradê escuro à esquerda e tipografia chamativa com borda preta
      │     • Salva imagem em 1280×720 (thumbnail.jpg)
      ▼
[ PASSO 5 ] Montagem Final do Vídeo com FFmpeg
      │     • Garante a presença da trilha instrumental em 'data/bg_music.mp3'
      │     • Cria sequência randômica longa sem repetição de clipe consecutivo
      │     • Mixa voz principal (1.0) com música de fundo sutil (0.18)
      │     • Renderiza legendas centralizadas com bordas nítidas
      │     • Exporta arquivo 1080p em H.264/AAC com flag '+faststart'
      ▼
[ PASSO 6 ] Agendamento e Publicação no YouTube
            • Renomeia o arquivo .mp4 para o título sanitizado do vídeo
            • Define privacidade como 'private' e calcula agendamento para 30 minutos à frente
            • Marca 'selfDeclaredMadeForKids: false'
            • Faz o upload resumable do vídeo e vincula a thumbnail personalizada
```

---

## 5. 🛡️ Políticas de Segurança, Anti-Reúso e Boas Práticas

1. **Quarentena de Vídeos (Anti-Reúso):** Nenhum vídeo do Pexels pode ser reutilizado antes de 5 dias corridos. O histórico é gravado em `data/videos_usados.json` e persistido no git.
2. **Transformações Audiovisuais:** Cada clipe de 5 segundos é esticado para ~6.25s (0.8x), espelhado e sem metadados para evitar penalizações de conteúdo duplicado.
3. **Imagens Seguras para Thumbnails:** Uso prioritário do acervo do Wikimedia Commons e Bing com `safeSearch=Strict` para evitar qualquer conteúdo impróprio.
4. **Respeito aos Limites da API:**
   - As tags do YouTube são limitadas e limpas de caracteres especiais para respeitar o limite máximo de 500 caracteres da API.
   - O título é limitado a no máximo 100 caracteres.
   - A descrição inclui estrutura pastoral, pedidos de engajamento, pedidos de oração nos comentários e hashtags estratégicas.
5. **Agendamento Inteligente:** O vídeo entra como privado e é programado para ir ao ar em 30 minutos (arredondado para a próxima meia hora), permitindo que o YouTube processe as versões em HD/4K antes de notificar os inscritos.

---

## 6. 🔐 Credenciais e Segredos Necessários

Para execução na nuvem (GitHub Actions) ou localmente (`.env`), as seguintes variáveis são utilizadas:

- `GROQ_API_KEY`: Acesso aos modelos `llama-3.3-70b-versatile` e `whisper-large-v3-turbo`.
- `PEXELS_API_KEY`: Busca e download de filmagens no Pexels.
- `YOUTUBE_API_KEY`: Consulta pública de dados de busca e visualizações no YouTube.
- `YOUTUBE_CLIENT_ID`: ID OAuth do projeto no Google Cloud Console.
- `YOUTUBE_CLIENT_SECRET`: Segredo do cliente OAuth no Google Cloud Console.
- `YOUTUBE_REFRESH_TOKEN`: Token de longa duração gerado via `scripts/obter_refresh_token.py`.
- `BING_SEARCH_API_KEY`: *(Opcional)* Busca de imagens complementares para thumbnails via Azure Cognitive Services.
