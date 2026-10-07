# Testes do cálculo de perfil (suitability.py).
#
# Como funciona o pytest:
# - ele procura arquivos que começam com "test_" e roda toda função que começa com "test_";
# - dentro de cada teste, "assert X" significa "X tem que ser verdadeiro";
# - se algum assert falhar, o pytest mostra qual teste quebrou e qual valor veio.

from suitability import calcular_suitability, classificar_score


# Função auxiliar: monta um dicionário de respostas com o mesmo valor em todas
# as perguntas. "alteracoes" permite trocar só as perguntas que interessam ao teste.
# Assim cada teste mostra apenas o que é diferente, sem repetir o dicionário inteiro.
def montar_respostas(valor_padrao, **alteracoes):
    respostas = {
        "renda": valor_padrao,
        "reserva": valor_padrao,
        "aporte": valor_padrao,
        "objetivo": valor_padrao,
        "experiencia": valor_padrao,
        "horizonte": valor_padrao,
        "tolerancia": valor_padrao,
        "perda_maxima": valor_padrao,
        "autopercep": valor_padrao,
    }
    respostas.update(alteracoes)
    return respostas


# ── 1. Limites do score ─────────────────────────────────────────

def test_score_minimo_e_conservador():
    # Todas as respostas = 1 → score mínimo (11).
    resultado = calcular_suitability(montar_respostas(1))
    assert resultado["score"] == 11
    assert resultado["perfil"] == "Conservador"


def test_score_maximo_e_agressivo():
    # Todas as respostas = 3 → score máximo (33), nenhuma restrição dispara.
    resultado = calcular_suitability(montar_respostas(3))
    assert resultado["score"] == 33
    assert resultado["perfil"] == "Agressivo"
    assert resultado["restricoes_aplicadas"] == []


def test_cortes_entre_perfis():
    # Confere as fronteiras: 18/19 e 26/27.
    # Se alguém mudar os cortes sem querer, este teste avisa.
    assert classificar_score(18) == "Conservador"
    assert classificar_score(19) == "Moderado"
    assert classificar_score(26) == "Moderado"
    assert classificar_score(27) == "Agressivo"


# ── 2. As três restrições ───────────────────────────────────────

def test_sem_reserva_limita_a_moderado():
    # Tudo 3, menos reserva = 1 → score 31 (seria Agressivo), mas cai para Moderado.
    resultado = calcular_suitability(montar_respostas(3, reserva=1))
    assert resultado["perfil_base"] == "Agressivo"
    assert resultado["perfil"] == "Moderado"
    assert "sem_reserva: teto moderado." in resultado["restricoes_aplicadas"]


def test_sem_experiencia_limita_a_moderado():
    # Tudo 3, menos experiencia = 1 → score 31, cai para Moderado.
    resultado = calcular_suitability(montar_respostas(3, experiencia=1))
    assert resultado["perfil_base"] == "Agressivo"
    assert resultado["perfil"] == "Moderado"
    assert "sem_experiencia: teto moderado." in resultado["restricoes_aplicadas"]


def test_horizonte_curto_forca_conservador():
    # Tudo 3, menos horizonte = 1 → score 29 (Agressivo), mas vira Conservador.
    resultado = calcular_suitability(montar_respostas(3, horizonte=1))
    assert resultado["perfil_base"] == "Agressivo"
    assert resultado["perfil"] == "Conservador"
    assert "horizonte_curto: teto conservador." in resultado["restricoes_aplicadas"]


# ── 3. Gap de calibração ────────────────────────────────────────

def test_gap_acentuado_quando_se_acha_agressivo():
    # Respostas conservadoras, mas a pessoa se declarou Agressiva (autopercep = 3).
    resultado = calcular_suitability(montar_respostas(1, autopercep=3))
    assert resultado["perfil"] == "Conservador"
    assert resultado["perfil_declarado"] == "Agressivo"
    assert resultado["tipo_gap"] == "gap acentuado"


def test_sem_gap_quando_autopercepcao_bate():
    resultado = calcular_suitability(montar_respostas(3, autopercep=3))
    assert resultado["gap_calibracao"] is False
    assert resultado["tipo_gap"] == "sem gap"
