# Testes do motor de alocação (allocation_engine.py).
# Nenhum teste aqui usa o banco: os ativos são passados direto para montar_carteira().

import pytest

from allocation_engine import alocacao_base, aplicar_restricoes_alocacao, montar_carteira


# Respostas "neutras": nenhuma restrição dispara. Cada teste muda só o que precisa.
def montar_respostas(**alteracoes):
    respostas = {"reserva": 3, "experiencia": 3, "horizonte": 3, "valor_invest": 10_000}
    respostas.update(alteracoes)
    return respostas


ATIVOS = [
    {"ticker": f"FII{i}11", "tipo_ativo": "fii", "nota": float(i),
     "dados": {"segmento": "tijolo", "dy_anual": 0.12}}
    for i in range(1, 7)   # 6 FIIs, notas de 1 a 6
]


# ── Config ──────────────────────────────────────────────────────

def test_cada_perfil_do_yaml_soma_100_por_cento():
    for perfil, fatias in alocacao_base.items():
        soma = fatias["fii"] + fatias["rf_longo"] + fatias["rf_curto"]
        assert soma == pytest.approx(1.0), perfil


# ── Restrições ──────────────────────────────────────────────────

def test_sem_reserva_eleva_liquidez_para_30():
    alocacao = {"fii": 0.30, "rf_longo": 0.50, "rf_curto": 0.20}
    alocacao, log = aplicar_restricoes_alocacao(alocacao, montar_respostas(reserva=1), [])
    assert alocacao["rf_curto"] == pytest.approx(0.30)
    assert sum(alocacao.values()) == pytest.approx(1.0)
    assert len(log) == 1


def test_horizonte_curto_zera_fii():
    alocacao = {"fii": 0.30, "rf_longo": 0.50, "rf_curto": 0.20}
    alocacao, log = aplicar_restricoes_alocacao(alocacao, montar_respostas(horizonte=1), [])
    assert alocacao["fii"] == 0
    assert alocacao["rf_curto"] == pytest.approx(0.50)


def test_restricao_nao_altera_o_yaml_carregado():
    # Montar uma carteira com restrição não pode mudar os percentuais base.
    antes = dict(alocacao_base["Moderado"])
    suit = {"perfil": "Moderado", "restricoes_aplicadas": []}
    montar_carteira(suit, montar_respostas(reserva=1), ativos=ATIVOS)
    assert alocacao_base["Moderado"] == antes


# ── Carteira completa ───────────────────────────────────────────

def test_carteira_usa_os_5_melhores_fiis():
    suit = {"perfil": "Agressivo", "restricoes_aplicadas": []}
    carteira = montar_carteira(suit, montar_respostas(), ativos=ATIVOS)
    tickers = [fii["ticker"] for fii in carteira["fiis"]]
    assert tickers == ["FII611", "FII511", "FII411", "FII311", "FII211"]


def test_inexperiente_recebe_no_maximo_3_fiis():
    suit = {"perfil": "Moderado", "restricoes_aplicadas": []}
    carteira = montar_carteira(suit, montar_respostas(experiencia=1), ativos=ATIVOS)
    assert len(carteira["fiis"]) == 3


def test_sem_fii_disponivel_nao_quebra():
    # Antes: 1 / len([]) → ZeroDivisionError. Agora: lista vazia.
    suit = {"perfil": "Agressivo", "restricoes_aplicadas": []}
    carteira = montar_carteira(suit, montar_respostas(), ativos=[])
    assert carteira["fiis"] == []


def test_valores_somam_o_capital():
    suit = {"perfil": "Moderado", "restricoes_aplicadas": []}
    carteira = montar_carteira(suit, montar_respostas(), ativos=ATIVOS)
    total = (sum(fii["valor"] for fii in carteira["fiis"])
             + carteira["rf_longo"]["valor"]
             + carteira["rf_curto"]["valor"])
    # Tolerância de R$ 1 por causa dos arredondamentos de centavos.
    assert total == pytest.approx(10_000, abs=1)
