# Contrato do ranking — o ponto de encontro entre a arquitetura e a análise.
#
# Quem implementa um ranking (ex.: FiiRanker) herda desta classe e preenche
# só dois métodos: filtrar() e pontuar(). Ordenar e cortar os N melhores
# já vem pronto aqui, igual para todo tipo de ativo.
#
# Formato de cada "ativo" (o mesmo que banco.buscar_ativos() devolve):
#   {"ticker": "HGLG11", "tipo_ativo": "fii", "nota": 9.2,
#    "dados": {"segmento": "logistica", "dy_anual": 0.11, ...}, ...}

from abc import ABC, abstractmethod


class BaseRanker(ABC):

    # Cada ranker diz qual tipo de ativo ele avalia ("fii", "acao", ...).
    # A classe filha OBRIGATORIAMENTE troca este None por um texto.
    tipo_ativo = None

    def __init__(self):
        # Checagem feita na criação do ranker: falha cedo, com mensagem clara,
        # se a classe filha esqueceu de definir tipo_ativo.
        if self.tipo_ativo is None:
            raise ValueError(
                f"{type(self).__name__} precisa definir o atributo tipo_ativo (ex.: 'fii')."
            )

    # ── Métodos que a classe filha PRECISA implementar ──────────

    @abstractmethod
    def filtrar(self, ativo):
        """
        Recebe UM ativo e devolve True se ele pode entrar no ranking,
        False se deve ser descartado (ex.: liquidez baixa demais).
        """

    @abstractmethod
    def pontuar(self, ativo):
        """
        Recebe UM ativo (já aprovado no filtro) e devolve a nota dele,
        um número de 0 a 10. Quanto maior, melhor.
        """

    # ── Métodos prontos, herdados por toda classe filha ─────────

    def ranquear(self, ativos):
        """
        Recebe a lista de ativos e devolve só os do tipo certo, aprovados
        no filtro, com a nota calculada e ordenados da maior para a menor.
        """
        ranqueados = []

        for ativo in ativos:
            # 1. Ignora ativos de outro tipo (um FiiRanker não avalia ações).
            if ativo["tipo_ativo"] != self.tipo_ativo:
                continue

            # 2. Descarta quem não passa no filtro da classe filha.
            if not self.filtrar(ativo):
                continue

            # 3. Copia o dicionário antes de mudar a nota, para não alterar
            #    a lista original que veio de fora (efeito colateral escondido).
            ativo_com_nota = dict(ativo)
            ativo_com_nota["nota"] = self.pontuar(ativo)
            ranqueados.append(ativo_com_nota)

        # 4. Ordena pela nota, da maior para a menor.
        ranqueados.sort(key=lambda ativo: ativo["nota"], reverse=True)
        return ranqueados

    def top_n(self, ativos, n):
        """Devolve os n melhores ativos do ranking."""
        return self.ranquear(ativos)[:n]
