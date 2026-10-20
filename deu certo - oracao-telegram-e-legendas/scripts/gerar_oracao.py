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
  "descricao": "Oração poderosa baseada no Salmo {salmo_info['numero']} para trazer bênçãos, proteção e quebra de amarras na sua vida e na sua família.",
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

    # ── Sanitização rigorosa da descrição (garantir que NUNCA vaze instruções de prompt) ──
    descricao = metadata.get("descricao", "")
    indicadores_prompt = [
        "PARÁGRAFO", "Hook SEO", "Escreva uma descrição", "seguir EXATAMENTE",
        "palavra-chave principal", "benefício emocional", "instrução espiritual",
        "estrutura:", "Oração poderosa baseada no Salmo"
    ]
    if any(ind.lower() in descricao.lower() for ind in indicadores_prompt) or len(descricao.strip()) < 150:
        print("[ORACAO] Descrição continha instruções de prompt ou era resumida. Aplicando descrição pastoral estruturada completa.")
        metadata["descricao"] = _gerar_descricao_completa(salmo_info, dia_semana_abrev)

    return metadata


def _gerar_descricao_completa(salmo_info: dict, dia_semana_abrev: str) -> str:
    """Gera uma descrição pastoral de alta conversão para o YouTube, rica em SEO e sem instruções cruas."""
    salmo_num = salmo_info["numero"]
    tema = salmo_info["tema"]
    keys = salmo_info["keys"]

    return (
        f"🙏 ORAÇÃO PODEROSA DO SALMO {salmo_num} — {tema.upper()} | {dia_semana_abrev}\n\n"
        f"Esta oração poderosa baseada no Salmo {salmo_num} foi preparada especialmente para o seu momento de fé hoje. "
        f"Se você precisa de {keys}, receba esta oração com o coração aberto. Não importa qual seja a tempestade, "
        f"a aflição ou a batalha na sua vida: quando você se coloca na presença do Altíssimo, todo jugo cai por terra. "
        f"Assista até o fim e receba a bênção de Deus agora mesmo.\n\n"
        f"📖 NESTE VÍDEO VOCÊ VAI RECEBER:\n"
        f"✅ A proclamação do Salmo {salmo_num} completo, versículo por versículo com reflexão pastoral\n"
        f"✅ Oração de autoridade espiritual pela {tema}\n"
        f"✅ Quebra de amarras espirituais, financeiras, familiares e de saúde\n"
        f"✅ Clamor e envio de anjos para guardar a sua casa e toda a sua família\n"
        f"✅ A oração do Pai Nosso completa para blindar o seu lar\n\n"
        f"🕊️ INSTRUÇÃO ESPIRITUAL PARA VITÓRIA:\n"
        f"Ouça esta oração por 7 dias consecutivos. Na Bíblia Sagrada, o número 7 representa a perfeição e o ciclo de vitória de Deus. "
        f"No momento da oração forte, erga a sua mão direita aos céus e repita as declarações de fé com determinação.\n\n"
        f"💬 COMENTE SEU NOME E PEDIDO DE ORAÇÃO:\n"
        f"Deixe nos comentários o seu nome e os nomes de seus familiares. Todos os dias esses nomes são apresentados diante de Deus em oração.\n\n"
        f"❤️ SEJA UM INSTRUMENTO DE BÊNÇÃO:\n"
        f"1. Deixe o seu LIKE — assim o YouTube entende que esta palavra abençoa vidas e recomenda para mais pessoas aflitas.\n"
        f"2. INSCREVA-SE no canal e ative o sininho para receber orações diárias de fé e vitória.\n"
        f"3. COMPARTILHE este vídeo no grupo da família e com amigos que precisam de um milagre hoje.\n\n"
        f"Que Jeová Rafá e o Deus de Israel abençoem grandemente a sua vida e toda a sua casa!\n\n"
        f"#oração #salmo{salmo_num} #oraçãoPoderosa #fé #Jesus #Deus #bênção #cura #proteção #oraçãoEvangélica #palavraDeDeus #milagre #quebraDeAmarras #oraçãoDoDia"
    )


def _metadata_padrao(salmo_info: dict) -> dict:
    dia_semana_abrev = DIAS_SEMANA[datetime.datetime.now().weekday()]
    return {
        "titulo": f"PODEROSA ORAÇÃO DO SALMO {salmo_info['numero']} — {salmo_info['tema'].upper()} | {dia_semana_abrev}",
        "descricao": _gerar_descricao_completa(salmo_info, dia_semana_abrev),
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
