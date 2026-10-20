import os
import re
import json
import random
import datetime

from groq import Groq

DIAS_SEMANA = ["SEGUNDA", "TERÇA", "QUARTA", "QUINTA", "SEXTA", "SÁBADO", "DOMINGO"]

# ─────────────────────────────────────────────────────────────────────────────
# Base de dados de salmos temáticos (rotação automática por dia do ano)
# ─────────────────────────────────────────────────────────────────────────────
SALMOS = [
    {"numero": "23",  "tema": "O Senhor é Meu Pastor",        "keys": "provisão, paz, restauração, conforto"},
    {"numero": "91",  "tema": "Proteção Divina e Familiar",   "keys": "proteção, amarras, casa, família"},
    {"numero": "121", "tema": "O Senhor Guarda Seus Passos",   "keys": "proteção, caminhos, saída e chegada"},
    {"numero": "27",  "tema": "O Senhor é Minha Luz",         "keys": "luz, salvação, vitória, confiança"},
    {"numero": "103", "tema": "Bênçãos e Cura Divina",        "keys": "cura, perdão, renovação, misericórdia"},
    {"numero": "46",  "tema": "Deus é Nosso Refúgio",         "keys": "refúgio, fortaleza, paz, força"},
    {"numero": "34",  "tema": "Libertação e Louvor",          "keys": "livramento, bênção, proteção, anjos"},
    {"numero": "18",  "tema": "Vitória Sobre os Inimigos",    "keys": "vitória, livramento, força, batalha"},
    {"numero": "37",  "tema": "Confie no Senhor",             "keys": "confiança, provisão, justiça, herança"},
    {"numero": "51",  "tema": "Arrependimento e Restauração", "keys": "perdão, restauração, novo coração"},
    {"numero": "63",  "tema": "Sede de Deus",                 "keys": "adoração, presença, sede espiritual"},
    {"numero": "139", "tema": "Deus Conhece o Seu Coração",   "keys": "onisciência, amor, ser conhecido por Deus"},
]


def gerar_oracao() -> dict:
    """
    Chama a API Groq e gera uma oração completa no estilo do canal Bispo Bruno Leonardo.
    Retorna um dict com: oracao_texto, titulo, descricao, tags, salmo, tema.
    """
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    # Seleciona o salmo do dia de forma rotativa e dia da semana
    dia_do_ano = datetime.datetime.now().timetuple().tm_yday
    salmo_info = SALMOS[dia_do_ano % len(SALMOS)]
    dia_semana_abrev = DIAS_SEMANA[datetime.datetime.now().weekday()]

    prompt = f"""Você é um pastor cristão evangélico brasileiro que grava orações poderosas no YouTube no estilo do canal "Bispo Bruno Leonardo".

Gere uma oração completa e emocionante baseada no Salmo {salmo_info['numero']} — "{salmo_info['tema']}".

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ESTRUTURA OBRIGATÓRIA (siga à risca):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. ABERTURA CALOROSA (3 parágrafos):
   - Cumprimento: "Olá, que Deus e os céus guardem a sua vida."
   - Apresente o Salmo {salmo_info['numero']} e seu poder ({salmo_info['keys']})
   - Convide para orar junto repetindo as palavras ou mentalmente
   - Peça para deixar nomes de familiares nos comentários
   - Explique que todos serão apresentados a Deus em oração

2. ENGAJAMENTO COM O CANAL (2 parágrafos):
   - Peça o gostei/like explicando que avisa o YouTube que o conteúdo é bom
   - Convide para se inscrever no canal para receber mais orações
   - Sugira ouvir esta oração por 7 dias seguidos (7 é o número de Deus)

3. SALMO {salmo_info['numero']} COMPLETO (versículo por versículo):
   - Leia todos os versículos com solene reverência
   - Após cada 2-3 versículos, insira uma breve reflexão pastoral

4. ORAÇÃO PESSOAL PODEROSA (8 a 10 parágrafos longos):
   - Use os nomes de Deus: Jeová Rafá, Jeová Jiré, Jeová Shalom, Jeová Eloí
   - Ore pela quebra de amarras: espirituais, familiares, financeiras, de saúde
   - Ore pela proteção da casa e família de quem está assistindo
   - Quebre obras malignas, maldições, feitiços, doenças
   - Use declarações: "Eu declaro que...", "Eu decreto que..."
   - Envie anjos guerreiros para proteger a pessoa e sua casa
   - Peça para a pessoa levantar a mão direita ao céu
   - Repita as declarações para a pessoa repetir em voz alta ou mentalmente

5. PAI NOSSO COMPLETO (texto completo, sem abreviações)

6. ENCERRAMENTO (3 parágrafos):
   - Confirme que as bênçãos estão sobre a vida, casa e família
   - Recomende ouvir por 7 dias consecutivos
   - Peça para compartilhar com familiares e amigos
   - "Que Jeová Rafá te abençoe grande e poderosamente. Até a próxima."

━━━━━━━━━━━━━━━━━━━━
REGRAS DE ESCRITA:
━━━━━━━━━━━━━━━━━━━━
- Tom: íntimo, pastoral, emotivo, cheio de fé e esperança
- Linguagem: português brasileiro formal-popular (pregação evangélica)
- MÍNIMO 2.500 palavras
- Parágrafos curtos (3-5 linhas cada) — facilitam leitura como legenda de vídeo
- SEM markdown, asteriscos, negrito ou formatação especial — apenas texto puro
- Parágrafo separado por linha em branco

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ao final do texto, adicione exatamente esta linha separadora e então o JSON:

---JSON---
{{
  "titulo": "PODEROSA ORAÇÃO DO SALMO {salmo_info['numero']} — {salmo_info['tema'].upper()} | {dia_semana_abrev}",
  "descricao": "Escreva uma descrição profissional de 350 a 450 palavras seguindo EXATAMENTE esta estrutura:\n\nPARÁGRAFO 1 (Hook SEO - 3 linhas): Comece com a palavra-chave principal (ex: 'Oração poderosa do Salmo {salmo_info['numero']}') + benefício emocional imediato + convite urgente para assistir.\n\nPARÁGRAFO 2 (O que você vai receber - 4 linhas): Descreva o que o vídeo contém: o Salmo {salmo_info['numero']} completo, oração pela {salmo_info['tema']}, quebra de amarras ({salmo_info['keys']}), bênção sobre a família.\n\nPARÁGRAFO 3 (Instrução espiritual - 3 linhas): Oriente a pessoa a ouvir por 7 dias seguidos, levantar a mão direita, repetir as declarações em voz alta.\n\nPARÁGRAFO 4 (Engajamento - 3 linhas): Peça o LIKE explicando que ajuda o canal a alcançar mais pessoas que precisam de oração. Convide para SE INSCREVER para receber orações diárias. Peça para deixar nomes nos comentários.\n\nPARÁGRAFO 5 (Compartilhamento - 2 linhas): Incentive compartilhar com família e amigos que precisam de uma palavra de fé hoje.\n\nFINAL: Adicione exatamente estas hashtags numa linha separada:\n#oração #salmo{salmo_info['numero']} #oraçãoPoderosa #fé #Jesus #Deus #bênção #cura #proteção #oraçãoEvangélica #palavraDeDeus #milagre #quebraDeAmarras #oraçãoDoDia",
  "tags": ["oração", "salmo {salmo_info['numero']}", "oração poderosa", "proteção", "família", "bênção", "cura", "quebrar amarras", "vitória", "oração do dia", "Deus", "fé", "palavra de Deus", "oração evangélica"],
  "salmo": "{salmo_info['numero']}",
  "tema": "{salmo_info['tema']}"
}}
"""

    modelos_candidatos = [
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-20b",
    ]

    response = None
    ultimo_erro = None
    for modelo in modelos_candidatos:
        try:
            print(f"[GROQ] Tentando modelo '{modelo}'...")
            response = client.chat.completions.create(
                model=modelo,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.72,
                max_tokens=4096,
            )
            print(f"[GROQ] Sucesso com o modelo '{modelo}'!")
            break
        except Exception as e:
            print(f"[GROQ] Falha no modelo '{modelo}': {e}")
            ultimo_erro = e

    if not response:
        raise RuntimeError(f"Nenhum modelo da Groq respondeu com sucesso. Último erro: {ultimo_erro}")

    content = response.choices[0].message.content.strip()

    # ── Separar texto da oração do JSON de metadados ──
    if "---JSON---" in content:
        partes = content.split("---JSON---", 1)
        oracao_texto = partes[0].strip()
        try:
            metadata = json.loads(partes[1].strip())
        except json.JSONDecodeError:
            metadata = _metadata_padrao(salmo_info)
    else:
        oracao_texto = content
        metadata = _metadata_padrao(salmo_info)

    metadata["oracao_texto"] = oracao_texto

    # ── Sanitização rigorosa do título (sem "Canal Oração", com DIA DA SEMANA) ──
    titulo = metadata.get("titulo", "")
    titulo = re.sub(r'\s*\|\s*canal\s+ora[çc][ãa]o\s*', '', titulo, flags=re.IGNORECASE)
    titulo = re.sub(r'\s*-\s*canal\s+ora[çc][ãa]o\s*', '', titulo, flags=re.IGNORECASE)
    titulo = re.sub(r'canal\s+ora[çc][ãa]o', '', titulo, flags=re.IGNORECASE).strip()
    if not any(titulo.upper().endswith(d) for d in DIAS_SEMANA):
        titulo = f"{titulo} | {dia_semana_abrev}"
    metadata["titulo"] = titulo

    return metadata


def _metadata_padrao(salmo_info: dict) -> dict:
    dia_semana_abrev = DIAS_SEMANA[datetime.datetime.now().weekday()]
    descricao_seo = (
        f"🙏 Oração Poderosa do Salmo {salmo_info['numero']} — {salmo_info['tema']}\n\n"
        f"Você está recebendo uma oração especial baseada no Salmo {salmo_info['numero']}, "
        f"preparada especialmente para trazer {salmo_info['keys']} para a sua vida e de toda a sua família. "
        f"Assista até o final e receba a bênção de Deus agora mesmo.\n\n"
        f"Nesta oração você vai receber:\n"
        f"✅ O Salmo {salmo_info['numero']} completo, versículo por versículo\n"
        f"✅ Oração poderosa pela {salmo_info['tema']}\n"
        f"✅ Quebra de amarras espirituais, financeiras e de saúde\n"
        f"✅ Bênção sobre sua casa, família e todos os seus filhos\n\n"
        f"👉 Ore por 7 dias seguidos para potencializar os resultados. "
        f"Levante sua mão direita ao céu e repita as declarações em voz alta.\n\n"
        f"❤️ Se esta oração te abençoou, dê um LIKE — isso avisa ao YouTube que este conteúdo "
        f"precisa chegar a mais pessoas que precisam de uma palavra de fé. "
        f"INSCREVA-SE no canal para receber novas orações todos os dias. "
        f"Deixe nos comentários o SEU NOME e o de seus familiares para receber oração especial.\n\n"
        f"🙌 Compartilhe com alguém que precisa de fé e de uma oração poderosa hoje.\n\n"
        f"#oração #salmo{salmo_info['numero']} #oraçãoPoderosa #fé "
        f"#Jesus #Deus #bênção #cura #proteção #oraçãoEvangélica #palavraDeDeus #milagre "
        f"#quebraDeAmarras #oraçãoDoDia"
    )
    return {
        "titulo": f"PODEROSA ORAÇÃO DO SALMO {salmo_info['numero']} — {salmo_info['tema'].upper()} | {dia_semana_abrev}",
        "descricao": descricao_seo,
        "tags": [
            "oração", f"salmo {salmo_info['numero']}", "oração poderosa",
            "proteção", "família", "bênção", "cura", "quebrar amarras",
            "vitória", "oração do dia", "Deus", "fé",
            "Jesus", "palavra de Deus", "milagre", "oração evangélica",
        ],
        "salmo": salmo_info["numero"],
        "tema": salmo_info["tema"],
    }


if __name__ == "__main__":
    import os, json
    os.makedirs("output", exist_ok=True)
    resultado = gerar_oracao()
    with open("output/oracao.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    print(f"✅ Oração gerada: {resultado['titulo']}")
    print(f"   Palavras: {len(resultado['oracao_texto'].split())}")
