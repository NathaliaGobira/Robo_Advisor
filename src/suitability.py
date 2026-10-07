# Cálculo do perfil do investidor, com bases que serão coletados no questionário.

PESOS = {
    "renda": 1,
    "reserva": 1,
    "aporte": 1,
    "objetivo": 1,
    "experiencia": 1,
    "horizonte": 2,
    "tolerancia": 2,
    "perda_maxima": 2
}

# Peso 1: situação financeira e experiência (renda, reserva, aporte, objetivo, experiencia).
# Peso 2: horizonte e reação a perdas (horizonte, tolerancia, perda_maxima).

# Score mínimo = (5*1)*1 + (1*3)*2 = 11
# Score máximo = (5*3)*1 + (3*3)*2 = 33

def classificar_score(score):
    if score <= 18:
        return "Conservador"
    elif score <= 26:
        return "Moderado"
    else:
        return "Agressivo"

# Regras para restrições

def aplica_restricao(perfil,resposta):

    restricoes_aplicadas = []

    #Regra 1: Se o investidor não tem reserva de emergência, não pode ser agressivo.

    if resposta["reserva"] == 1 and perfil == "Agressivo":
        perfil = "Moderado"
        restricoes_aplicadas.append("sem_reserva: teto moderado.")

    # Regra 2: Se o investidor não tem experiência, não pode ser agressivo.

    if resposta["experiencia"] == 1 and perfil == "Agressivo":
        perfil = "Moderado"
        restricoes_aplicadas.append("sem_experiencia: teto moderado.")

    # Regra 3: Se o investidor tem horizonte curto, seu perfil é conservador

    if resposta["horizonte"] == 1:
        perfil = "Conservador"
        restricoes_aplicadas.append("horizonte_curto: teto conservador.")

    return perfil, restricoes_aplicadas

# Ver distância entre o cálculo do perfil e a autopercepção do investidor

autopercep_map = {
    1: "Conservador",
    2: "Moderado",
    3: "Agressivo"
}

def calcular_distancia(perfil_calculado, autopercep):

    perfil_declarado = autopercep_map[autopercep]
    ordem = {"Conservador": 1, "Moderado": 2, "Agressivo": 3}
    distancia = abs(ordem[perfil_calculado] - ordem[perfil_declarado])
    diferenca = ordem[perfil_calculado] - ordem[perfil_declarado]

    if distancia == 0:
        tipo_gap = "sem gap"
    elif distancia == 1:
        tipo_gap = "gap leve"
    else:
        tipo_gap = "gap acentuado"

    # direção do gap
    if diferenca > 0:
        direcao = "subestimou"   # se achou mais conservador do que é
    elif diferenca < 0:
        direcao = "superestimou" # se achou mais arrojado do que é
    else:
        direcao = "calibrado"    

    return {
        "perfil_declarado": perfil_declarado,
        "gap": perfil_declarado != perfil_calculado,
        "tipo_gap": tipo_gap,
        "distancia": distancia,
        "direcao_gap": direcao
    }

# Função para calcular o score do investidor

def calcular_suitability(resposta):

    # Calcular o score do investidor

    score = sum(
        resposta[pergunta] * peso 
        for pergunta, peso in PESOS.items()
    )

    # Classificar o perfil do investidor aplicando as regras de restrição

    perfil_base = classificar_score(score)
    perfil_final, restricoes = aplica_restricao(perfil_base, resposta)

    gap = calcular_distancia(perfil_final, resposta["autopercep"])

    resultado = {
        "perfil": perfil_final,
        "score": score,
        "perfil_base": perfil_base,
        "restricoes_aplicadas": restricoes,
        "perfil_declarado": gap["perfil_declarado"],
        "gap_calibracao": gap["gap"],
        "tipo_gap": gap["tipo_gap"],
    }

    return resultado

#--------------------------------------

def exibir_resultados(resultado, nome):

    emoji = {
        "Conservador": "🟢",
        "Moderado": "🟡",   
        "Agressivo": "🔴"
    }

    perfil = resultado["perfil"]

    print("\n" + "=" * 50)
    print(f" RESULTADO - {nome.upper()}")
    print("=" * 50)
    print(f" Perfil calculado: {emoji.get(perfil,'⚪')} {perfil.upper()}")
    print(f" Score: {resultado['score']}pontos")
    print(f" Perfil declarado: {resultado['perfil_declarado']}")

    if resultado["gap_calibracao"]:
        print(f" Gap de Calibração: {resultado['tipo_gap']}")
    else:
        print(f" Gap de calibração: sem gap")

    if resultado["restricoes_aplicadas"]:
        print(f"\n Restrições aplicadas:")
        for r in resultado["restricoes_aplicadas"]:
            print(f"    • {r}")    


    print("=" * 50)


#-------------------------
if __name__ =="__main__":
    from questionario_v1 import coletar_perfil

    resposta = coletar_perfil()
    resultado = calcular_suitability(resposta)
    exibir_resultados(resultado, resposta["nome"])

    print("\n Dicionário completo para o banco de dados:")
    for chave, valor in resultado.items():
        print(f"{chave:<22} {valor}")