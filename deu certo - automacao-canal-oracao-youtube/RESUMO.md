# ✅ Deu Certo — Automação do Canal Oração com Upload no YouTube e Thumbnail

**Data:** 2026-06-25 22:43 (BRT)  
**Projeto:** Canal Oração (robsonvit/canal-oracao)

## O que funcionou

Foi implementado com sucesso o pipeline automatizado de geração de conteúdo para o canal de orações no YouTube. A automação executa as seguintes etapas:
1. **Geração do Texto da Oração:** Uso do modelo `llama-3.3-70b` da Groq AI para redação do salmo e descrição.
2. **Geração de Áudio e Legenda:** Síntese de voz grave realista via Edge-TTS e geração automática do arquivo de legenda SRT sincronizado.
3. **Clipes de Vídeo:** Busca e otimização automatizada de múltiplos clipes de plano de fundo religiosos/ambientais da plataforma Pexels.
4. **Thumbnail Personalizada:** Criação dinâmica da miniatura do vídeo com overlay de texto (Salmo, tema) usando Pillow.
5. **Montagem do Vídeo:** Renderização final em 1080p integrando vídeo, áudio, trilha sonora e legenda embutida usando FFmpeg.
6. **Upload Automático:** Envio direto do vídeo e da miniatura personalizada (thumbnail) para a API do YouTube v3 via OAuth2.
7. **Automação Diária:** Orquestração completa rodando via GitHub Actions todos os dias às 06:00 BRT.

> [!IMPORTANT]
> **Solução do Problema de Thumbnail:**
> A miniatura não estava sendo enviada inicialmente porque a conta do YouTube necessitava de **verificação de telefone** no painel do YouTube Studio para liberar o upload de imagens personalizadas. Após a verificação de número telefônico em `youtube.com/verify`, a API do YouTube passou a aceitar a thumbnail com sucesso.

---

## Arquivos envolvidos

| Arquivo/Pasta | Papel na solução |
| :--- | :--- |
| `scripts/pipeline.py` | Orquestrador principal que executa todos os passos na sequência correta. |
| `scripts/gerar_oracao.py` | Redige o texto usando a API do Groq e estrutura o JSON da oração. |
| `scripts/gerar_audio.py` | Gera a locução e o arquivo SRT. |
| `scripts/buscar_video.py` | Busca, baixa e corta os clipes de vídeo usando a API do Pexels. |
| `scripts/gerar_capa.py` | Gera a imagem `thumbnail.jpg` baseada nos metadados do salmo. |
| `scripts/montar_video.py` | Concatena clipes e aplica a trilha sonora/legenda usando FFmpeg. |
| `scripts/upload_youtube.py` | Envia o vídeo finalizado e a thumbnail gerada usando a API do YouTube. |
| `scripts/obter_refresh_token.py` | Utilitário local para autenticar a conta do Google e gerar o token OAuth2. |
| `.github/workflows/main.yml` | Workflow do GitHub Actions para execução diária na nuvem. |
| `requirements.txt` | Lista de dependências e bibliotecas Python necessárias. |

---

## Como replicar

1. **Instalar Dependências:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Configuração de API e Secrets:**
   Configure as chaves nos Secrets do GitHub ou crie variáveis de ambiente locais:
   - `GROQ_API_KEY`
   - `PEXELS_API_KEY`
   - `YOUTUBE_CLIENT_ID` (Google Cloud Developer Console)
   - `YOUTUBE_CLIENT_SECRET` (Google Cloud Developer Console)
   - `YOUTUBE_REFRESH_TOKEN` (Gerado a partir do script `obter_refresh_token.py`)
3. **Verificação do Canal:**
   Garantir que a conta do YouTube associada está devidamente verificada por telefone em `https://www.youtube.com/verify`.
4. **Execução:**
   ```bash
   python scripts/pipeline.py
   ```

---

## Observações

- A verificação do canal é mandatória para aceitar custom thumbnails via API. Sem isso, a chamada `youtube.thumbnails().set()` retornará erro 403.
- Os tokens expiram em nível de permissão caso o escopo mude. Caso necessite gerenciar listas ou novos tipos de uploads, lembre-se de rodar novamente o `obter_refresh_token.py` adicionando os escopos corretos à variável `SCOPES`.
