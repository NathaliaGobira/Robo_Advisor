# Este código monta a carteira do investidor a partir de dados do perfil

# Os dados usados são mock por enquanto. Os FIIs estão sendo avaliados e os demais são só para teste

FIIS = [
    {"ticker": "HGLG11", "tipo": "logistica",  "dy_anual": 0.11, "nota": 9.2},
    {"ticker": "KNRI11", "tipo": "hibrido",    "dy_anual": 0.09, "nota": 8.8},
    {"ticker": "XPML11", "tipo": "shopping",   "dy_anual": 0.10, "nota": 8.5},
    {"ticker": "BCFF11", "tipo": "fof",        "dy_anual": 0.12, "nota": 8.1},
    {"ticker": "MXRF11", "tipo": "recebivel",  "dy_anual": 0.13, "nota": 7.9},
]

RENDA_FIXA = [
    {"nome": "Tesouro IPCA+ 2035",  "tipo": "longo_prazo", "taxa": "IPCA + 6,2%", "liquidez": "no_vencimento"},
    {"nome": "CDB 120% CDI 2 anos", "tipo": "longo_prazo", "taxa": "120% CDI",    "liquidez": "no_vencimento"},
    {"nome": "Tesouro Selic 2026",  "tipo": "curto_prazo", "taxa": "100% Selic",  "liquidez": "diaria"},
    {"nome": "CDB liquidez diária", "tipo": "curto_prazo", "taxa": "100% CDI",    "liquidez": "diaria"},
]


# Alocação método heurística para definição de carteiras

# fii       → fundos imobiliários (maior risco, maior retorno potencial)
# rf_longo  → renda fixa longo prazo (travado até vencimento)
# rf_curto  → renda fixa curto prazo / liquidez imediata

alocacao_base = {
    "Conservador": {
        "fii":      0.10,
        "rf_longo": 0.50,
        "rf_curto": 0.40,
        "descricao": "Prioridade em segurança e liquidez.",
    },
    "Moderado": {
        "fii":      0.30,
        "rf_longo": 0.50,
        "rf_curto": 0.20,
        "descricao": "Equilíbrio entre renda e crescimento.",
    },
    "Agressivo": {
        "fii":      0.55,
        "rf_longo": 0.35,
        "rf_curto": 0.10,
        "descricao": "Foco em crescimento patrimonial.",
    },
}


#  Aplicação de restrições na alocação 

def aplicar_restricoes_alocacao(alocacao, respostas, restricoes_log):
    """
    Recebe os percentuais base e ajusta conforme as respostas brutas.
    Retorna os percentuais ajustados e o log atualizado.

    Os ajustes redistribuem percentual entre as fatias para
    que a soma continue em 1.0.
    """

    # Restrição A: sem reserva de emergência (aumenta liquidez imediata para pelo menos 30%, reduzindo da rf_longa)
    
    if respostas["reserva"] == 1 and alocacao["rf_curto"] < 0.30:
        diferenca = 0.30 - alocacao["rf_curto"]
        alocacao["rf_curto"] += diferenca
        alocacao["rf_longo"] -= diferenca
        restricoes_log.append("sem_reserva: rf_curto elevado para 30%")

    # Restrição B: inexperiente (limita FIIs a no máximo 3 ativos, FII no máximo 20%)

    if respostas["experiencia"] == 1 and alocacao["fii"] > 0.20:
        diferenca = alocacao["fii"] - 0.20
        alocacao["fii"]      -= diferenca
        alocacao["rf_longo"] += diferenca
        restricoes_log.append("sem_experiencia: fii limitado a 20%")

    # Restrição C: horizonte curto (Sem FIIs) 

    if respostas["horizonte"] == 1 and alocacao["fii"] > 0:
        alocacao["rf_curto"] += alocacao["fii"]
        alocacao["fii"]       = 0.0
        restricoes_log.append("horizonte_curto: fii zerado, capital em rf_curto")

    return alocacao, restricoes_log


# SELEÇÃO DOS FIIS 

def selecionar_fiis(respostas, valor_fii):
    
    limite = 3 if respostas["experiencia"] == 1 else 5

    top_fiis     = sorted(FIIS, key=lambda x: x["nota"], reverse=True)[:limite]
    peso_por_fii = round(1 / len(top_fiis), 4)

    fiis_selecionados = []
    for fii in top_fiis:
        valor_alocado = valor_fii * peso_por_fii
        dy_mensal     = valor_alocado * fii["dy_anual"] / 12
        fiis_selecionados.append({
            "ticker":        fii["ticker"],
            "tipo":          fii["tipo"],
            "nota":          fii["nota"],
            "peso":          peso_por_fii,
            "valor":         round(valor_alocado, 2),
            "dy_mensal_est": round(dy_mensal, 2),
        })

    return fiis_selecionados


# SELEÇÃO DA RENDA FIXA 

def selecionar_renda_fixa(tipo, valor):
    
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


# ──────────────────────────────────────────

def montar_carteira(resultado_suitability, respostas):
    
    perfil   = resultado_suitability["perfil"]
    capital  = respostas["valor_invest"]

    # cópia dos percentuais base para não alterar o original
    alocacao = dict(alocacao_base[perfil])
    descricao = alocacao.pop("descricao")  # separa a descrição dos números

    # restrições herdadas do suitability (para registrar junto)
    restricoes_log = list(resultado_suitability["restricoes_aplicadas"])

    # aplica restrições específicas de alocação
    alocacao, restricoes_log = aplicar_restricoes_alocacao(
        alocacao, respostas, restricoes_log
    )

    # calcula os valores em reais
    v_fii      = capital * alocacao["fii"]
    v_rf_longo = capital * alocacao["rf_longo"]
    v_rf_curto = capital * alocacao["rf_curto"]

    # seleciona os ativos
    fiis     = selecionar_fiis(respostas, v_fii) if v_fii > 0 else []
    rf_longo = selecionar_renda_fixa("longo_prazo", v_rf_longo)
    rf_curto = selecionar_renda_fixa("curto_prazo", v_rf_curto)

    return {
        "perfil":              perfil,
        "descricao_perfil":    descricao,
        "capital":             capital,
        "pct_fii":             alocacao["fii"],
        "pct_rf_longo":        alocacao["rf_longo"],
        "pct_rf_curto":        alocacao["rf_curto"],
        "fiis":                fiis,
        "rf_longo":            rf_longo,
        "rf_curto":            rf_curto,
        "restricoes_ativadas": restricoes_log,
    }


# Carteira

def exibir_carteira(carteira, nome):
    """
    Imprime a carteira recomendada de forma legível no terminal.
    """
    print("\n" + "=" * 52)
    print(f"  CARTEIRA RECOMENDADA — {nome.upper()}")
    print("=" * 52)
    print(f"  Perfil:  {carteira['perfil'].upper()}")
    print(f"  Capital: R$ {carteira['capital']:,.2f}")
    print(f"  Obs:     {carteira['descricao_perfil']}")

    # FIIs
    v_fii = carteira["capital"] * carteira["pct_fii"]
    print(f"\n  FIIs ({carteira['pct_fii']*100:.0f}%)  →  R$ {v_fii:,.2f}")
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
    if carteira["rf_longo"]:
        rf = carteira["rf_longo"]
        print(f"    {rf['nome']} | {rf['taxa']} | liquidez: {rf['liquidez']}")

    # Renda fixa curto prazo
    v_rf_curto = carteira["capital"] * carteira["pct_rf_curto"]
    print(f"\n  Renda fixa curto prazo / liquidez ({carteira['pct_rf_curto']*100:.0f}%)  →  R$ {v_rf_curto:,.2f}")
    if carteira["rf_curto"]:
        rf = carteira["rf_curto"]
        print(f"    {rf['nome']} | {rf['taxa']} | liquidez: {rf['liquidez']}")

    # Restrições aplicadas
    if carteira["restricoes_ativadas"]:
        print(f"\n  Restrições aplicadas:")
        for r in carteira["restricoes_ativadas"]:
            print(f"    • {r}")

    print("=" * 52)


#----------------------------------------------------

if __name__ == "__main__":
    from questionario_v1 import coletar_perfil
    from suitability     import calcular_suitability, exibir_resultados

    resposta  = coletar_perfil()
    resultado  = calcular_suitability(resposta)

    exibir_resultados(resultado, resposta["nome"])

    carteira = montar_carteira(resultado, resposta)
    exibir_carteira(carteira, resposta["nome"])