from questionario_v1  import coletar_perfil
from suitability      import calcular_suitability, exibir_resultados
from allocation_engine import montar_carteira, exibir_carteira
from banco            import (
    criar_tabelas,
    salvar_cliente,
    salvar_questionario,
    salvar_carteira,
    registrar_evento,
    popular_ativos_mock,
)


def inicializar():
    criar_tabelas()
    popular_ativos_mock()


# Fluxo principal do programa

def executar():

    print("\n" + "=" * 52)
    print("  ROBO ADVISOR — Bem-vindo")
    print("=" * 52)
    print("  Vamos montar a sua carteira personalizada.")
    print("  Responda as perguntas a seguir com calma.\n")

    # etapa 1: coleta de dados 

    resposta = coletar_perfil()

    # etapa 2: salva o cliente no banco 
    cliente_id = salvar_cliente(resposta)

    # etapa 3: calcula o suitability 
    resultado = calcular_suitability(resposta)

    # etapa 4: exibe o resultado do perfil 
    exibir_resultados(resultado, resposta["nome"])

    # etapa 5: salva o questionário no banco 
    questionario_id = salvar_questionario(cliente_id, resposta, resultado)

    # etapa 6: monta a carteira
    carteira = montar_carteira(resultado, resposta)

    # etapa 7: exibe a carteira 

    exibir_carteira(carteira, resposta["nome"])

    # etapa 8: salva a carteira no banco
    salvar_carteira(cliente_id, questionario_id, carteira)

    # etapa 9: registra evento inicial 
    registrar_evento(
        cliente_id,
        tipo="cadastro_completo",
        detalhe=f"perfil: {resultado['perfil']} | score: {resultado['score']}"
    )

    # encerramento
    
    print("\n" + "=" * 52)
    print("  Processo concluído.")
    print(f"  Dados salvos para: {resposta['nome']}")
    print("=" * 52 + "\n")


# ── EXECUÇÃO ─────────────────────────────────────────────────

if __name__ == "__main__":
    inicializar()
    executar()