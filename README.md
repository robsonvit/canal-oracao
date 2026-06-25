# 🙏 Canal Oração — Automação de Vídeos Diários

Pipeline automático que gera e publica **uma oração diária no YouTube** usando:
- **Groq AI** (llama-3.3-70b) para gerar o texto da oração
- **edge-tts** para síntese de voz grave masculina
- **Pexels API** para vídeos de natureza suaves como fundo
- **FFmpeg** para montagem do vídeo 1920×1080 com legendas centralizadas
- **YouTube Data API v3** para publicação automática

---

## 📋 Como Configurar (Passo a Passo)

### 1. Criar Repositório no GitHub

```bash
# No terminal, dentro da pasta do projeto:
git init
git add .
git commit -m "🙏 Canal Oração — configuração inicial"
git remote add origin https://github.com/SEU_USUARIO/canal-oracao.git
git push -u origin main
```

---

### 2. Obter API Key gratuita do Pexels

1. Acesse [pexels.com/api](https://www.pexels.com/api/)
2. Crie uma conta gratuita
3. Copie a sua API Key (plano grátis = 200 req/hora)

---

### 3. Configurar credenciais do YouTube (OAuth 2.0)

#### 3.1 — Google Cloud Console

1. Acesse [console.cloud.google.com](https://console.cloud.google.com/)
2. Crie um novo projeto: `Canal Oração`
3. Vá em **APIs e Serviços → Biblioteca**
4. Ative a **YouTube Data API v3**
5. Vá em **APIs e Serviços → Credenciais**
6. Clique em **Criar Credenciais → ID do cliente OAuth 2.0**
7. Tipo: **Aplicativo para computador (Desktop)**
8. Anote o **Client ID** e **Client Secret**

#### 3.2 — Gerar o Refresh Token (local)

```bash
# Instale a dependência localmente
pip install google-auth-oauthlib

# Execute o script (abre o navegador)
python scripts/obter_refresh_token.py
```

- Faça login com `robsonvitaacademico@gmail.com`
- Autorize o acesso ao YouTube
- Copie o **REFRESH TOKEN** exibido no terminal

---

### 4. Configurar Secrets no GitHub

Vá em: **GitHub → Seu repositório → Settings → Secrets and variables → Actions**

Adicione estes secrets (botão **New repository secret**):

| Secret | Valor |
|--------|-------|
| `GROQ_API_KEY` | *(sua chave groq api)* |
| `PEXELS_API_KEY` | *(sua chave do pexels.com/api)* |
| `YOUTUBE_CLIENT_ID` | *(do Google Cloud Console)* |
| `YOUTUBE_CLIENT_SECRET` | *(do Google Cloud Console)* |
| `YOUTUBE_REFRESH_TOKEN` | *(gerado pelo script local)* |

---

### 5. Ativar o Workflow

O workflow é executado **automaticamente todo dia às 06:00 BRT**.

Para testar manualmente:
1. Vá em **GitHub → Actions → 🙏 Gerar Oração Diária**
2. Clique em **Run workflow → Run workflow**

---

## 🎬 O que o Pipeline Faz

```
06:00 BRT (todo dia)
    │
    ├─ 1. Groq AI gera oração (Salmo rotativo, ~2.500 palavras)
    │
    ├─ 2. edge-tts converte em áudio grave (pt-BR-AntonioNeural)
    │       + gera legendas SRT com timestamps de palavras
    │
    ├─ 3. Pexels API busca 12 vídeos de natureza suave
    │       • Respeita bloqueio de 5 dias por vídeo
    │       • Cada clipe: 5s originais → hflip → 0.8x velocidade
    │       • Remove metadados de cada clipe
    │
    ├─ 4. Pillow gera thumbnail 1280×720
    │       (estilo: foto escura de bíblia + texto dourado)
    │
    ├─ 5. FFmpeg monta vídeo 1920×1080
    │       • Concatena os 12 clipes (~75s de conteúdo único)
    │       • Faz loop até cobrir toda a duração do áudio
    │       • Legendas centralizadas (fonte serif branca, borda preta)
    │       • Mixagem com áudio TTS
    │
    └─ 6. YouTube API publica o vídeo
            + define thumbnail personalizada
            + salva tracking de vídeos usados no repositório
```

---

## 📁 Estrutura do Projeto

```
CANAL ORAÇÃO/
├── .github/
│   └── workflows/
│       └── gerar_oracao_diaria.yml   ← Workflow principal
│
├── scripts/
│   ├── pipeline.py                   ← Orquestrador
│   ├── gerar_oracao.py               ← Groq AI
│   ├── gerar_audio.py                ← TTS + SRT
│   ├── buscar_video.py               ← Pexels + transformações
│   ├── gerar_capa.py                 ← Thumbnail
│   ├── montar_video.py               ← FFmpeg
│   ├── upload_youtube.py             ← YouTube API
│   └── obter_refresh_token.py        ← [Local] OAuth helper
│
├── data/
│   └── videos_usados.json            ← Tracking de vídeos (atualizado a cada run)
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🔄 Controle de Reuso de Vídeos

O sistema rastreia em `data/videos_usados.json` todos os vídeos usados:

```json
{
  "1234567": "2026-06-24T09:00:00+00:00",
  "7654321": "2026-06-23T09:00:00+00:00"
}
```

Um vídeo só pode ser reutilizado **após 5 dias** do último uso.
Este arquivo é atualizado e commitado automaticamente a cada execução.

---

## 🎬 Transformações Aplicadas em Cada Clipe

Cada vídeo baixado do Pexels recebe:
1. **Corte de 5 segundos** em posição aleatória do vídeo
2. **Espelho horizontal** (`hflip`) — evita detecção de reuso
3. **Velocidade 0.8×** (`setpts=1.25*PTS`) — ritmo mais contemplativo
4. **Remoção de metadados** (`-map_metadata -1`) — privacidade

Resultado: cada clipe tem ~6.25 segundos (5s ÷ 0.8 = 6.25s)

---

## ⚙️ Configurações Ajustáveis

Em `scripts/buscar_video.py`:
- `NUM_CLIPS = 12` — quantidade de clipes por vídeo
- `DIAS_BLOQUEIO = 5` — dias antes de reusar um vídeo
- `DURACAO_CLIP_S = 5` — segundos de filmagem original por clipe

Em `scripts/gerar_audio.py`:
- `PITCH = "-10Hz"` — tom da voz (mais negativo = mais grave)
- `RATE = "-8%"` — ritmo da voz
- `PALAVRAS_POR_LEGENDA = 7` — palavras por bloco de legenda

---

## 📞 Suporte

Para dúvidas sobre configuração, consulte:
- [Groq Cloud](https://console.groq.com/)
- [Pexels API](https://www.pexels.com/api/)
- [Google Cloud Console](https://console.cloud.google.com/)
- [YouTube Data API](https://developers.google.com/youtube/v3)
