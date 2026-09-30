import sqlite3
import json
from datetime import date
from pathlib import Path

# Caminho do banco ancorado na raiz do projeto (uma pasta acima de src/).
# Assim o banco fica sempre no mesmo lugar, rode de onde rodar.
DB_PATH = Path(__file__).resolve().parent.parent / "robo_advisor.db"


def conectar():
    """
    Abre a conexão com o banco e retorna o objeto de conexão.
    Sempre feche a conexão após usar: conn.close()
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # permite acessar colunas pelo nome
    return conn


# Criando as tabelas

def criar_tabelas():
    """
    Cria todas as tabelas do banco na primeira execução.
    Execute isso uma vez antes de começar a usar o sistema.
    """
    conn = conectar()

    conn.executescript("""

        -- Tabela 1: clientes
        -- Dados de identificação. O email é o identificador único.
        CREATE TABLE IF NOT EXISTS clientes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            nome       TEXT    NOT NULL,
            email      TEXT    NOT NULL UNIQUE,
            criado_em  TEXT    NOT NULL
        );

        -- Tabela 2: questionarios
        -- Cada vez que o cliente responde, gera um novo registro.
        -- Nunca sobrescreve o anterior — mantém o histórico completo.
        CREATE TABLE IF NOT EXISTS questionarios (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id          INTEGER NOT NULL,
            respondido_em       TEXT    NOT NULL,
            renda               INTEGER NOT NULL,
            reserva             INTEGER NOT NULL,
            aporte              INTEGER NOT NULL,
            objetivo            INTEGER NOT NULL,
            horizonte           INTEGER NOT NULL,
            experiencia         INTEGER NOT NULL,
            tolerancia          INTEGER NOT NULL,
            perda_maxima        INTEGER NOT NULL,
            autopercep          INTEGER NOT NULL,
            patrimonio          REAL    NOT NULL,
            valor_invest        REAL    NOT NULL,
            score               INTEGER NOT NULL,
            perfil_base         TEXT    NOT NULL,
            perfil_final        TEXT    NOT NULL,
            perfil_declarado    TEXT    NOT NULL,
            gap_calibracao      INTEGER NOT NULL,
            tipo_gap            TEXT    NOT NULL,
            restricoes_ativadas TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        );

        -- Tabela 3: carteiras
        -- Cada carteira gerada fica registrada permanentemente.
        -- Ligada ao questionário que a originou.
        CREATE TABLE IF NOT EXISTS carteiras (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id       INTEGER NOT NULL,
            questionario_id  INTEGER NOT NULL,
            gerada_em        TEXT    NOT NULL,
            perfil           TEXT    NOT NULL,
            capital          REAL    NOT NULL,
            pct_fii          REAL    NOT NULL,
            pct_rf_longo     REAL    NOT NULL,
            pct_rf_curto     REAL    NOT NULL,
            fiis             TEXT,
            rf_longo         TEXT,
            rf_curto         TEXT,
            restricoes       TEXT,
            FOREIGN KEY (cliente_id)      REFERENCES clientes(id),
            FOREIGN KEY (questionario_id) REFERENCES questionarios(id)
        );

        -- Tabela 4: eventos_cliente
        -- Registra comportamentos reais do cliente dentro do sistema.
        -- Ex: pediu revisão, rejeitou um FII, refez o questionário.
        -- Base para análise comportamental futura.
        CREATE TABLE IF NOT EXISTS eventos_cliente (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id   INTEGER NOT NULL,
            tipo         TEXT    NOT NULL,
            ocorrido_em  TEXT    NOT NULL,
            detalhe      TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        );

        -- Tabela 5: ativos
        -- Alimentada pelo colega com os dados reais dos FIIs.
        -- Por enquanto populada com dados mock.
        CREATE TABLE IF NOT EXISTS ativos (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker        TEXT    NOT NULL UNIQUE,
            tipo_ativo    TEXT    NOT NULL,        -- 'fii', 'acao', 'renda_fixa'...
            nome          TEXT,
            nota          REAL,                    -- aguardando avaliação
            dados_json    TEXT,                    -- Caracteriticas especificas dos ativos, em JSON
            atualizado_em TEXT    NOT NULL
        );
        
    """)

    conn.commit()
    conn.close()
    print("✓ Tabelas criadas com sucesso.")


# Cliente

def salvar_cliente(resposta):
    """
    Insere um cliente novo no banco.
    Se o email já existir, não duplica — apenas avisa.

    Parâmetro:
        resposta (dict) — saída de coletar_perfil()

    Retorna:
        id do cliente no banco (int)
    """
    conn = conectar()

    try:
        cursor = conn.execute(
            "INSERT INTO clientes (nome, email, criado_em) VALUES (?, ?, ?)",
            (resposta["nome"], resposta["email"], date.today().isoformat())
        )
        conn.commit()
        cliente_id = cursor.lastrowid
        print(f"✓ Cliente '{resposta['nome']}' salvo. ID: {cliente_id}")

    except sqlite3.IntegrityError:
        # email já existe — busca o id do cliente existente
        row = conn.execute(
            "SELECT id FROM clientes WHERE email = ?",
            (resposta["email"],)
        ).fetchone()
        cliente_id = row["id"]
        print(f"  Cliente já cadastrado. ID: {cliente_id}")

    finally:
        conn.close()

    return cliente_id


def buscar_cliente_por_email(email):
    """
    Busca um cliente pelo email.
    Retorna o registro completo ou None se não encontrado.
    """
    conn = conectar()
    row  = conn.execute(
        "SELECT * FROM clientes WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# Questionários

def salvar_questionario(cliente_id, resposta, resultado):
    """
    Salva as respostas do questionário e o resultado do suitability.
    Sempre cria um novo registro — nunca sobrescreve o anterior.

    Parâmetros:
        cliente_id (int)   — id retornado por salvar_cliente()
        resposta   (dict)  — saída de coletar_perfil()
        resultado  (dict)  — saída de calcular_suitability()

    Retorna:
        id do questionário no banco (int)
    """
    conn = conectar()

    cursor = conn.execute("""
        INSERT INTO questionarios (
            cliente_id, respondido_em,
            renda, reserva, aporte, objetivo, horizonte,
            experiencia, tolerancia, perda_maxima, autopercep,
            patrimonio, valor_invest,
            score, perfil_base, perfil_final,
            perfil_declarado, gap_calibracao, tipo_gap,
            restricoes_ativadas
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?
        )
    """, (
        cliente_id,
        date.today().isoformat(),
        resposta["renda"],
        resposta["reserva"],
        resposta["aporte"],
        resposta["objetivo"],
        resposta["horizonte"],
        resposta["experiencia"],
        resposta["tolerancia"],
        resposta["perda_maxima"],
        resposta["autopercep"],
        resposta["patrimonio"],
        resposta["valor_invest"],
        resultado["score"],
        resultado["perfil_base"],
        resultado["perfil"],
        resultado["perfil_declarado"],
        int(resultado["gap_calibracao"]),       # True/False → 1/0
        resultado["tipo_gap"],
        json.dumps(resultado["restricoes_aplicadas"])  # lista → texto JSON
    ))

    conn.commit()
    questionario_id = cursor.lastrowid
    conn.close()

    print(f"✓ Questionário salvo. ID: {questionario_id}")
    return questionario_id


# ── CARTEIRAS ─────────────────────────────────────────────────

def salvar_carteira(cliente_id, questionario_id, carteira):
    """
    Salva a carteira recomendada pelo motor de alocação.

    Parâmetros:
        cliente_id      (int)  — id do cliente
        questionario_id (int)  — id do questionário que originou a carteira
        carteira        (dict) — saída de montar_carteira()

    Retorna:
        id da carteira no banco (int)
    """
    conn = conectar()

    cursor = conn.execute("""
        INSERT INTO carteiras (
            cliente_id, questionario_id, gerada_em,
            perfil, capital,
            pct_fii, pct_rf_longo, pct_rf_curto,
            fiis, rf_longo, rf_curto, restricoes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cliente_id,
        questionario_id,
        date.today().isoformat(),
        carteira["perfil"],
        carteira["capital"],
        carteira["pct_fii"],
        carteira["pct_rf_longo"],
        carteira["pct_rf_curto"],
        json.dumps(carteira["fiis"]),            # lista → texto JSON
        json.dumps(carteira["rf_longo"]),        # dict  → texto JSON
        json.dumps(carteira["rf_curto"]),        # dict  → texto JSON
        json.dumps(carteira["restricoes_ativadas"])
    ))

    conn.commit()
    carteira_id = cursor.lastrowid
    conn.close()

    print(f"✓ Carteira salva. ID: {carteira_id}")
    return carteira_id


# Eventos

def registrar_evento(cliente_id, tipo, detalhe=None):
    """
    Registra um comportamento real do cliente no sistema.
    Chame isso sempre que o cliente fizer algo relevante.

    Tipos sugeridos:
        "pediu_revisao"     — cliente voltou e pediu nova avaliação
        "aceitou_carteira"  — cliente confirmou que seguiu a recomendação
        "rejeitou_fii"      — cliente pediu para remover um FII
        "refez_questionario"— cliente respondeu novamente

    Parâmetros:
        cliente_id (int) — id do cliente
        tipo       (str) — tipo do evento
        detalhe    (str) — observação livre, opcional
    """
    conn = conectar()

    conn.execute(
        "INSERT INTO eventos_cliente (cliente_id, tipo, ocorrido_em, detalhe) VALUES (?, ?, ?, ?)",
        (cliente_id, tipo, date.today().isoformat(), detalhe)
    )

    conn.commit()
    conn.close()
    print(f"✓ Evento '{tipo}' registrado para cliente ID {cliente_id}.")


# ── FIIS RANKING ──────────────────────────────────────────────

def popular_ativos_mock():
    """
    Insere os FIIs simulados no banco para testes.
    Quando o colega entregar os dados reais, substituir por:
        popular_fiis_csv("ranking_fiis.csv")
    """
    FIIS_MOCK = [
        {"ticker": "HGLG11", "nota": 9.2, "dados": {"segmento": "logistica", "dy_anual": 0.11}},
        {"ticker": "KNRI11", "nota": 8.8, "dados": {"segmento": "hibrido", "dy_anual": 0.09}},
        {"ticker": "XPML11", "nota": 8.5, "dados": {"segmento": "shopping", "dy_anual": 0.10}},
        {"ticker": "BCFF11", "nota": 8.1, "dados": {"segmento": "fof", "dy_anual": 0.12}},
        {"ticker": "MXRF11", "nota": 7.9, "dados": {"segmento": "recebivel", "dy_anual": 0.13}},
    ]

    conn = conectar()

    for fii in FIIS_MOCK:
        # INSERT OR IGNORE: se o ticker já existe (viola o UNIQUE), o banco
        # ignora a linha em vez de dar erro. Rodar 2x não duplica.
        conn.execute ("""
            INSERT OR IGNORE INTO ativos (ticker, tipo_ativo, nota,
            dados_json, atualizado_em)
            VALUES (?, ?, ?, ?, ?)
            """, (
            fii["ticker"],
            "fii",                    
            fii["nota"],
            json.dumps(fii["dados"]),  
            date.today().isoformat()
        ))

    conn.commit()
    conn.close()
    
    print(f"✓ {len(FIIS_MOCK)} FIIs mock inseridos no banco.")


def buscar_ativos():
    """
    Retorna todos os FIIs do banco ordenados por nota (maior primeiro).
    Usado pela alocação para buscar os dados do banco em vez do mock local.
    """
    conn  = conectar()
    rows  = conn.execute(
        "SELECT * FROM ativos ORDER BY nota DESC"
    ).fetchall()
    conn.close()

    ativos = []
    for row in rows:
        ativo = dict(row)      #Transforma a linha em dicionario
    
    #Desempacota os dados do arquivo json    
    
        if ativo["dados_json"]:
            ativo["dados"] = json.loads(ativo["dados_json"])
        else:
            ativo["dados"] = {}

        ativos.append(ativo)

    return ativos


# ── CONSULTAS ÚTEIS ───────────────────────────────────────────

def historico_cliente(email):
    """
    Mostra todos os questionários e carteiras de um cliente.
    Útil para acompanhar a evolução do perfil ao longo do tempo.
    """
    conn    = conectar()
    cliente = conn.execute(
        "SELECT * FROM clientes WHERE email = ?", (email,)
    ).fetchone()

    if not cliente:
        print(f"  Cliente '{email}' não encontrado.")
        conn.close()
        return

    questionarios = conn.execute(
        "SELECT * FROM questionarios WHERE cliente_id = ? ORDER BY respondido_em",
        (cliente["id"],)
    ).fetchall()

    conn.close()

    print(f"\n{'='*50}")
    print(f"  HISTÓRICO — {cliente['nome'].upper()}")
    print(f"{'='*50}")
    for q in questionarios:
        print(f"\n  Data:   {q['respondido_em']}")
        print(f"  Perfil: {q['perfil_final']}  (score: {q['score']})")
        print(f"  Gap:    {q['tipo_gap']}")


# ── EXECUÇÃO STANDALONE ───────────────────────────────────────
# Roda para criar o banco e popular os FIIs mock.
# Execute uma vez antes de usar o sistema completo:
#   python3 banco.py

if __name__ == "__main__":
    print("\nIniciando configuração do banco de dados...")
    criar_tabelas()
    popular_ativos_mock()
    print("\n✓ Banco pronto em: robo_advisor.db")
    print("  Próximo passo: python3 main.py\n")