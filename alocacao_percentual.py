# Recomendação de alocação por percentuais — sem seleção de ativos específicos

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

COMENTARIOS = {
    "fii":      "Fundos imobiliários — renda passiva mensal com maior potencial de valorização.",
    "rf_longo": "Renda fixa longo prazo — retorno previsível, capital travado até o vencimento.",
    "rf_curto": "Renda fixa curto prazo — liquidez imediata para imprevistos e oportunidades.",
}


def aplicar_restricoes_alocacao(alocacao, respostas, restricoes_log):

    if respostas["reserva"] == 1 and alocacao["rf_curto"] < 0.30:
        diferenca = 0.30 - alocacao["rf_curto"]
        alocacao["rf_curto"] += diferenca
        alocacao["rf_longo"] -= diferenca
        restricoes_log.append("sem_reserva: rf_curto elevado para 30% — você ainda não tem reserva de emergência.")

    if respostas["experiencia"] == 1 and alocacao["fii"] > 0.20:
        diferenca = alocacao["fii"] - 0.20
        alocacao["fii"]      -= diferenca
        alocacao["rf_longo"] += diferenca
        restricoes_log.append("sem_experiencia: FIIs limitados a 20% — recomendado para quem está começando.")

    if respostas["horizonte"] == 1 and alocacao["fii"] > 0:
        alocacao["rf_curto"] += alocacao["fii"]
        alocacao["fii"]       = 0.0
        restricoes_log.append("horizonte_curto: FIIs zerados — com menos de 2 anos, liquidez é prioridade.")

    return alocacao, restricoes_log


def recomendar_alocacao(resultado_suitability, respostas):

    perfil   = resultado_suitability["perfil"]
    capital  = respostas["valor_invest"]

    alocacao  = dict(alocacao_base[perfil])
    descricao = alocacao.pop("descricao")

    restricoes_log = list(resultado_suitability["restricoes_aplicadas"])

    alocacao, restricoes_log = aplicar_restricoes_alocacao(
        alocacao, respostas, restricoes_log
    )

    return {
        "perfil":              perfil,
        "descricao_perfil":    descricao,
        "capital":             capital,
        "pct_fii":             alocacao["fii"],
        "pct_rf_longo":        alocacao["rf_longo"],
        "pct_rf_curto":        alocacao["rf_curto"],
        "restricoes_ativadas": restricoes_log,
    }


def exibir_alocacao(rec, nome):

    print("\n" + "=" * 52)
    print(f"  ALOCAÇÃO RECOMENDADA — {nome.upper()}")
    print("=" * 52)
    print(f"  Perfil:  {rec['perfil'].upper()}")
    print(f"  Capital: R$ {rec['capital']:,.2f}")
    print(f"  Obs:     {rec['descricao_perfil']}")

    print("\n  Distribuição sugerida:\n")

    fatias = [
        ("FIIs",                    "pct_fii",      "fii"),
        ("Renda fixa longo prazo",  "pct_rf_longo", "rf_longo"),
        ("Renda fixa curto prazo",  "pct_rf_curto", "rf_curto"),
    ]

    for label, pct_key, comentario_key in fatias:
        pct   = rec[pct_key]
        valor = rec["capital"] * pct
        print(f"  {label}: {pct*100:.0f}%  →  R$ {valor:,.2f}")
        print(f"    {COMENTARIOS[comentario_key]}\n")

    if rec["restricoes_ativadas"]:
        print("  Ajustes aplicados ao seu perfil:")
        for r in rec["restricoes_ativadas"]:
            print(f"    • {r}")

    print("=" * 52)


if __name__ == "__main__":
    from questionario_v1 import coletar_perfil
    from suitability     import calcular_suitability, exibir_resultados

    resposta  = coletar_perfil()
    resultado = calcular_suitability(resposta)

    exibir_resultados(resultado, resposta["nome"])

    rec = recomendar_alocacao(resultado, resposta)
    exibir_alocacao(rec, resposta["nome"])
