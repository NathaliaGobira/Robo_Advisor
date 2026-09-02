import unicodedata

#Normalização e sanitização de strings

def normalizar(texto):
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        c for c in texto
        if unicodedata.category(c) != "Mn"
    )
    return texto.strip()    

def capitalizar_nome(texto):
    return texto.strip().title()

# Validação de inputs

def perguntar_opcao(pergunta, opcoes):

    print(f"\n{pergunta}")
    for i, opcao in enumerate(opcoes, start=1):
        print(f"   {i} - {opcao}")

    while True:
        entrada = input(f"   Escolha (1-{len(opcoes)}): ").strip()

        if not entrada.isdigit():
            print(f"   ⚠ Digite apenas o número da opção.")
            continue

        escolha = int(entrada)
        if 1 <= escolha <= len(opcoes):
            return escolha
        else:
            print(f"   ⚠ Opção inválida. Escolha entre 1 e {len(opcoes)}.")

def perguntar_valor(pergunta, minimo=0):

    while True:
        entrada = input(f"\n{pergunta}R$ ").strip()
        entrada = entrada.replace(",", ".")  # para aceitar vírgula ou ponto decimal

        try:
            valor = float(entrada)
            if valor >= minimo:
                return valor
            else:
                print(f"   ⚠ O valor deve ser maior que R$ {minimo:,.2f}.")
        except ValueError:
            print("   ⚠ Digite um valor numérico. Ex: 5000 ou 5000.50")

def perguntar_email():

    while True:
        email = input("\nSeu email (será seu identificador único): ").strip()
        email_norm = normalizar(email)

        if "@" in email_norm and "."  in email_norm:
            return email_norm
        else:
            print("   ⚠ Email inválido. Ex: joao@gmail.com")   

# Questionário de perfil do usuário

def coletar_perfil():
    print("\n" + "="*50)
    print("  ROBO ADVISOR - Perfil do Investidor")
    print("=" * 50)

    nome_digitado = input("\nSeu nome completo:").strip()
    nome          = capitalizar_nome(nome_digitado)
    email         = perguntar_email()

    print(f"\n  Olá, {nome}! Vamos montar o seu perfil.")

    #Situação Financeira  

    print("\n A. Situação financeira " + "─" * 26)

    renda = perguntar_opcao(
        "1. Qual é a sua renda mensal líquida?",
        ["Até R$ 3.000",
         "De R$ 3.000 até R$ 10.000",
         "Acima de R$ 10.000"]          
    )

    reserva = perguntar_opcao(
        "2. Você possui reserva de emergência (mínimo 6 meses de despesas)?",
        ["Não tenho reserva",
         "Tenho menos de 6 meses",
         "Tenho 6 meses ou mais"]
    )

    aporte = perguntar_opcao(
        "3. Qual percentual da sua renda consegue investir por mês?",
        ["Menos de 10%",
         "Entre 10% e 30%",
         "Mais de 30%"]
    )

    #Objetivos

    print("\n B. Objetivos e Horizonte " + "─" * 26)
    
    objetivo = perguntar_opcao(
        "4. Qual é o seu objetivo principal?",
        ["Preservar o capital. Perder o mínimo possível",
         "Equilibrar segurança e crescimento",
         "Maximizar crescimento no longo prazo"]
    )
    
    horizonte = perguntar_opcao(
        "5. Em quanto tempo vai precisar deste dinheiro?",
        ["Menos de 2 anos",
         "Entre 2 e 5 anos",
         "Mais de 5 anos"]
    )
    
    #Conhecimento e Riscos

    print("\n C. Conhecimento e tolerância ao risco " + "─" * 26)
    
    experiencia = perguntar_opcao(
        "6. Você já investiu em algum dos programas abaixo?",
        ["Nunca investi em nada além de Poupança",
         "Já investi em renda fixa (CDB, Tesouro) ou fundos",
         "Já investi em ações, FIIs ou produtos mais complexos"]
    )
    
    tolerancia = perguntar_opcao(
        "7. Se investir R$ 10.000,00, e, após três meses, ver que este valor caiu para R$ 8.500,00. O que você faz?",
        ["Venderia tudo imediatamente.",
         "Ficaria preocupado, mas aguardaria",
         "Aproveitaria para comprar mais"]
    )

    perda_maxima = perguntar_opcao(
        "8. Qual é a perda máxima em 12 meses que você consegue aceitar?",
        ["Nenhuma. Preciso presercar o valor",
         "Até 15% de perda temporária",
         "Mais de 15% se o potencial de ganho for alto"]
    )

    # Autopercepção para análises futuras

    autopercep = perguntar_opcao(
        "9. Antes de calcular, qual perfil você acredita que tem?",
        ["Conservador. Priorizo segurança acima de tudo",
         "Moderado. Busco equilíbrio entre segurança e crescimento",
         "Agressivo. Aceito riscos maiores por retornos maiores"]
    )

    #Dados financeiros

    print("\n Dados financeiros " + "─" * 30)
    patrimonio = perguntar_valor("Patrimônio total: ", minimo=0)
    valor_invest = perguntar_valor("Valor a investir: ", minimo=1)

    return {
        "nome": nome,
        "email": email,     
        "renda": renda,
        "reserva": reserva,
        "aporte": aporte,
        "objetivo": objetivo,
        "horizonte": horizonte,
        "experiencia": experiencia,
        "tolerancia": tolerancia,
        "perda_maxima": perda_maxima,
        "autopercep": autopercep,
        "patrimonio": patrimonio,
        "valor_invest": valor_invest,
    }

if __name__ == "__main__":
    perfil = coletar_perfil()

    print("\n" + "="*50)
    print("Dados Coletados:")
    print("="*50)
    for chave, valor in perfil.items():
        print(f"{chave:<15}{valor}")
