# Testes do contrato de ranking (base_ranker.py).
#
# Para testar uma classe abstrata, criamos aqui um ranker de mentira, bem simples.
# Ele também serve de EXEMPLO para o colega: é assim que um ranker real é escrito.

import pytest

from base_ranker import BaseRanker


# ── Ranker de exemplo ───────────────────────────────────────────

class RankerDividendos(BaseRanker):
    tipo_ativo = "fii"

    def filtrar(self, ativo):
        # Só aceita FIIs com dividend yield de pelo menos 10% ao ano.
        return ativo["dados"]["dy_anual"] >= 0.10

    def pontuar(self, ativo):
        # Nota = DY × 50, limitada a 10 (10% → 5.0; 13% → 6.5; 20% ou mais → 10).
        return min(ativo["dados"]["dy_anual"] * 50, 10)


# Dados de teste no mesmo formato de banco.buscar_ativos().
ATIVOS = [
    {"ticker": "KNRI11", "tipo_ativo": "fii",  "nota": None, "dados": {"dy_anual": 0.09}},
    {"ticker": "HGLG11", "tipo_ativo": "fii",  "nota": None, "dados": {"dy_anual": 0.10}},
    {"ticker": "XPML11", "tipo_ativo": "fii",  "nota": None, "dados": {"dy_anual": 0.095}},
    {"ticker": "MXRF11", "tipo_ativo": "fii",  "nota": None, "dados": {"dy_anual": 0.13}},
    {"ticker": "PETR4",  "tipo_ativo": "acao", "nota": None, "dados": {"dy_anual": 0.20}},
]


# ── O contrato é obrigatório ────────────────────────────────────
# pytest.raises(Erro) significa: "o código dentro do bloco TEM que dar este erro".

def test_nao_da_para_usar_a_classe_base_direto():
    with pytest.raises(TypeError):
        BaseRanker()


def test_classe_filha_sem_pontuar_e_recusada():
    class RankerIncompleto(BaseRanker):
        tipo_ativo = "fii"

        def filtrar(self, ativo):
            return True
        # faltou pontuar()

    with pytest.raises(TypeError):
        RankerIncompleto()


def test_classe_filha_sem_tipo_ativo_e_recusada():
    class RankerSemTipo(BaseRanker):
        def filtrar(self, ativo):
            return True

        def pontuar(self, ativo):
            return 5

    with pytest.raises(ValueError):
        RankerSemTipo()


# ── O comportamento herdado ─────────────────────────────────────

def test_ranquear_filtra_pontua_e_ordena():
    resultado = RankerDividendos().ranquear(ATIVOS)
    tickers = [ativo["ticker"] for ativo in resultado]

    # KNRI11 e XPML11 caem no filtro (DY < 10%); PETR4 é de outro tipo.
    # MXRF11 (nota 6.5) vem antes de HGLG11 (nota 5.0).
    assert tickers == ["MXRF11", "HGLG11"]
    assert resultado[0]["nota"] == pytest.approx(6.5)


def test_top_n_respeita_o_limite():
    resultado = RankerDividendos().top_n(ATIVOS, 1)
    assert len(resultado) == 1
    assert resultado[0]["ticker"] == "MXRF11"


def test_ranquear_nao_altera_a_lista_original():
    RankerDividendos().ranquear(ATIVOS)
    # As notas originais continuam None: o ranker trabalhou em cópias.
    assert all(ativo["nota"] is None for ativo in ATIVOS)
