# Motor de alocação: transforma o perfil do investidor numa carteira.
#
# Junta o que antes estava espalhado em alocacao_teste.py e alocacao_percentual.py:
#   1. lê os percentuais por perfil do config/allocation.yaml
#   2. aplica as restrições (sem reserva, sem experiência, horizonte curto)
#   3. escolhe os ativos de cada fatia (FIIs via ranker, renda fixa via lista)

import yaml
from pathlib import Path

import banco
from nota_banco_ranker import NotaBancoRanker

# Caminho do config ancorado na raiz do projeto (uma pasta acima de src/).
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "allocation.yaml"

# Ranker usado quando ninguém informa outro. Trocar aqui quando o do colega chegar.
RANKER_FII_PADRAO = NotaBancoRanker

# Renda fixa ainda fixa no código — virá do adapter do Tesouro Direto no futuro.
RENDA_FIXA = [
    {"nome": "Tesouro IPCA+ 2035",  "tipo": "longo_prazo", "taxa": "IPCA + 6,2%", "liquidez": "no_vencimento"},
    {"nome": "CDB 120% CDI 2 anos", "tipo": "longo_prazo", "taxa": "120% CDI",    "liquidez": "no_vencimento"},
    {"nome": "Tesouro Selic 2026",  "tipo": "curto_prazo", "taxa": "100% Selic",  "liquidez": "diaria"},
    {"nome": "CDB liquidez diária", "tipo": "curto_prazo", "taxa": "100% CDI",    "liquidez": "diaria"},
]

COMENTARIOS = {
    "fii":      "Fundos imobiliários — renda passiva mensal com maior potencial de valorização.",
    "rf_longo": "Renda fixa longo prazo — retorno previsível, capital travado até o vencimento.",
    "rf_curto": "Renda fixa curto prazo — liquidez imediata para imprevistos e oportunidades.",
}


# ── 1. Percentuais por perfil ───────────────────────────────────

def carregar_alocacao_base():
    """Lê o YAML e devolve o dicionário {perfil: {fii, rf_longo, rf_curto, descricao}}."""
    with open(CONFIG_PATH, encoding="utf-8") as arquivo:
        config = yaml.safe_load(arquivo)
    return config["perfil"]


# Lido uma vez, quando o módulo é importado.
alocacao_base = carregar_alocacao_base()


# ── 2. Restrições ───────────────────────────────────────────────

def aplicar_restricoes_alocacao(alocacao, respostas, restricoes_log):
    """
    Ajusta os percentuais conforme as respostas brutas do questionário.
    Cada ajuste tira de uma fatia e põe em outra, então a soma continua 1.0.
    """

    # Restrição A: sem reserva de emergência → pelo menos 30% com liquidez diária.
    if respostas["reserva"] == 1 and alocacao["rf_curto"] < 0.30:
        diferenca = 0.30 - alocacao["rf_curto"]
        alocacao["rf_curto"] += diferenca
        alocacao["rf_longo"] -= diferenca
        restricoes_log.append("sem_reserva: rf_curto elevado para 30%")

    # Restrição B: sem experiência → FII no máximo 20%.
    if respostas["experiencia"] == 1 and alocacao["fii"] > 0.20:
        diferenca = alocacao["fii"] - 0.20
        alocacao["fii"]      -= diferenca
        alocacao["rf_longo"] += diferenca
        restricoes_log.append("sem_experiencia: fii limitado a 20%")

    # Restrição C: horizonte curto → sem FII, tudo que era FII vai para liquidez.
    if respostas["horizonte"] == 1 and alocacao["fii"] > 0:
        alocacao["rf_curto"] += alocacao["fii"]
        alocacao["fii"]       = 0.0
        restricoes_log.append("horizonte_curto: fii zerado, capital em rf_curto")

    return alocacao, restricoes_log


def recomendar_alocacao(resultado_suitability, respostas):
    """
    Só os percentuais, sem escolher ativos (o que alocacao_percentual.py fazia).
    Também é o primeiro passo de montar_carteira().
    """
    perfil = resultado_suitability["perfil"]

    # Cópia: sem ela, as restrições alterariam alocacao_base para os próximos clientes.
    alocacao  = dict(alocacao_base[perfil])
    descricao = alocacao.pop("descricao")

    restricoes_log = list(resultado_suitability["restricoes_aplicadas"])
    alocacao, restricoes_log = aplicar_restricoes_alocacao(alocacao, respostas, restricoes_log)

    return {
        "perfil":              perfil,
        "descricao_perfil":    descricao,
        "capital":             respostas["valor_invest"],
        "pct_fii":             alocacao["fii"],
        "pct_rf_longo":        alocacao["rf_longo"],
        "pct_rf_curto":        alocacao["rf_curto"],
        "restricoes_ativadas": restricoes_log,
    }


# ── 3. Seleção dos ativos ───────────────────────────────────────

def selecionar_fiis(respostas, valor_fii, ativos, ranker):
    """Escolhe os melhores FIIs pelo ranker e divide o valor igualmente entre eles."""

    limite = 3 if respostas["experiencia"] == 1 else 5
    top_fiis = ranker.top_n(ativos, limite)

    # Proteção: se nenhum FII passou no filtro, não há o que dividir
    # (sem isso, 1 / len([]) daria ZeroDivisionError).
    if not top_fiis:
        return []

    peso_por_fii = round(1 / len(top_fiis), 4)

    fiis_selecionados = []
    for fii in top_fiis:
        valor_alocado = valor_fii * peso_por_fii
        dy_mensal = valor_alocado * fii["dados"]["dy_anual"] / 12
        fiis_selecionados.append({
            "ticker":        fii["ticker"],
            "tipo":          fii["dados"]["segmento"],
            "nota":          fii["nota"],
            "peso":          peso_por_fii,
            "valor":         round(valor_alocado, 2),
            "dy_mensal_est": round(dy_mensal, 2),
        })

    return fiis_selecionados


def selecionar_renda_fixa(tipo, valor):
    """Por enquanto pega a primeira opção do tipo pedido."""
    opcoes = [rf for rf in RENDA_FIXA if rf["tipo"] == tipo]
    if not opcoes:
        return None

    escolha = opcoes[0]
    return {
        "nome":     escolha["nome"],
        "taxa":     escolha["taxa"],
        "liquidez": escolha["liquidez"],
        "valor":    round(valor, 2),
    }


# ── 4. Carteira completa ────────────────────────────────────────

def montar_carteira(resultado_suitability, respostas, ativos=None, ranker=None):
    """
    Monta a carteira completa: percentuais + ativos escolhidos.

    ativos e ranker são opcionais:
      - se não vierem, busca os ativos no banco e usa o RANKER_FII_PADRAO;
      - se vierem, usa os informados (é assim que os testes rodam sem banco).
    """
    if ativos is None:
        ativos = banco.buscar_ativos()
    if ranker is None:
        ranker = RANKER_FII_PADRAO()

    carteira = recomendar_alocacao(resultado_suitability, respostas)

    capital    = carteira["capital"]
    v_fii      = capital * carteira["pct_fii"]
    v_rf_longo = capital * carteira["pct_rf_longo"]
    v_rf_curto = capital * carteira["pct_rf_curto"]

    if v_fii > 0:
        carteira["fiis"] = selecionar_fiis(respostas, v_fii, ativos, ranker)
    else:
        carteira["fiis"] = []
    carteira["rf_longo"] = selecionar_renda_fixa("longo_prazo", v_rf_longo)
    carteira["rf_curto"] = selecionar_renda_fixa("curto_prazo", v_rf_curto)

    return carteira


# ── 5. Exibição no terminal ─────────────────────────────────────

def exibir_carteira(carteira, nome):
    """Imprime a carteira recomendada de forma legível no terminal."""
    print("\n" + "=" * 52)
    print(f"  CARTEIRA RECOMENDADA — {nome.upper()}")
    print("=" * 52)
    print(f"  Perfil:  {carteira['perfil'].upper()}")
    print(f"  Capital: R$ {carteira['capital']:,.2f}")
    print(f"  Obs:     {carteira['descricao_perfil']}")

    # FIIs
    v_fii = carteira["capital"] * carteira["pct_fii"]
    print(f"\n  FIIs ({carteira['pct_fii']*100:.0f}%)  →  R$ {v_fii:,.2f}")
    print(f"    {COMENTARIOS['fii']}")
    if carteira["fiis"]:
        for fii in carteira["fiis"]:
            print(f"    {fii['ticker']:<8} nota {fii['nota']} "
                  f"| R$ {fii['valor']:>10,.2f} "
                  f"| DY est. R$ {fii['dy_mensal_est']:,.2f}/mês")
    else:
        print("    Nenhum FII alocado para este perfil.")

    # Renda fixa longo prazo
    v_rf_longo = carteira["capital"] * carteira["pct_rf_longo"]
    print(f"\n  Renda fixa longo prazo ({carteira['pct_rf_longo']*100:.0f}%)  →  R$ {v_rf_longo:,.2f}")
    print(f"    {COMENTARIOS['rf_longo']}")
    if carteira["rf_longo"]:
        rf = carteira["rf_longo"]
        print(f"    {rf['nome']} | {rf['taxa']} | liquidez: {rf['liquidez']}")

    # Renda fixa curto prazo
    v_rf_curto = carteira["capital"] * carteira["pct_rf_curto"]
    print(f"\n  Renda fixa curto prazo / liquidez ({carteira['pct_rf_curto']*100:.0f}%)  →  R$ {v_rf_curto:,.2f}")
    print(f"    {COMENTARIOS['rf_curto']}")
    if carteira["rf_curto"]:
        rf = carteira["rf_curto"]
        print(f"    {rf['nome']} | {rf['taxa']} | liquidez: {rf['liquidez']}")

    # Restrições aplicadas
    if carteira["restricoes_ativadas"]:
        print("\n  Restrições aplicadas:")
        for r in carteira["restricoes_ativadas"]:
            print(f"    • {r}")

    print("=" * 52)
