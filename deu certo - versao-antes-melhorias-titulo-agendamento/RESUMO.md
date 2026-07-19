# ✅ Deu Certo — Versão Antes das Melhorias de Título e Agendamento

**Data:** 2026-06-29 18:41 BRT  
**Projeto:** Canal Oração — Automação YouTube

## O que estava funcionando

Pipeline completo de automação do canal cristão no YouTube:
- Geração de oração com Groq AI (llama-3.3-70b)
- Geração de áudio TTS + legendas SRT (edge-tts)
- Busca e processamento de clipes do Pexels (hflip + 0.8x + 5s)
- Geração de thumbnail personalizada com Pillow
- Montagem de vídeo final 1920×1080 com FFmpeg
- Upload para o YouTube via YouTube Data API v3 com publicação imediata

## Arquivos envolvidos

| Arquivo | Papel na solução |
|---------|-----------------|
| `scripts/pipeline.py` | Orquestrador principal — chama todos os passos em sequência |
| `scripts/gerar_oracao.py` | Gera oração via Groq AI, retorna título/descrição/tags |
| `scripts/upload_youtube.py` | Faz upload e define thumbnail no YouTube, publica imediatamente |
| `requirements.txt` | Dependências do projeto |

## Melhorias planejadas (próximo passo)

1. **Título baseado em pesquisa de concorrentes** — pesquisa YouTube pelo tema, filtra mais visualizados, escreve título 90% similar
2. **Renomear arquivo de vídeo** com o título final antes do upload
3. **Descrição com SEO** — estrutura profissional com palavras-chave
4. **Agendamento** — em vez de publicar agora, agenda para 30 min após conclusão
5. **Tags ampliadas** — tags básicas do canal + tags dos vídeos mais visualizados do tema
6. **Marcar "não é para crianças"** — já feito, mas revisar o campo correto

## Observações

- O upload atual publica o vídeo imediatamente como `public`
- O título atual segue o padrão `PODEROSA ORAÇÃO DO SALMO X — TEMA | Canal Oração`
- Tags atuais são genéricas, não baseadas em pesquisa de concorrentes
