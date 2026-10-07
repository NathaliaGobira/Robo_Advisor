# Ranker PROVISÓRIO de FIIs.
#
# Usa a nota que já está gravada no banco (tabela ativos, coluna nota),
# sem calcular nada. Existe só para a alocação já funcionar pelo contrato
# BaseRanker enquanto o ranker real do colega não chega.
#
# Quando o FiiRanker do colega existir, basta trocar este ranker por ele
# em allocation_engine.py (constante RANKER_FII_PADRAO).

from base_ranker import BaseRanker


class NotaBancoRanker(BaseRanker):
    tipo_ativo = "fii"

    def filtrar(self, ativo):
        # Aceita todo FII que tenha nota (descarta os ainda não avaliados).
        return ativo["nota"] is not None

    def pontuar(self, ativo):
        # Repete a nota do banco.
        return ativo["nota"]
