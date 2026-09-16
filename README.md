# Robo Advisor

Robô que identifica o perfil do investidor a partir de um questionário e recomenda uma carteira de investimentos compatível — começando por FIIs e renda fixa, com expansão prevista para outros ativos.

Projeto colaborativo e exploratório (aprendizado). Requisito central de design: crescer sem retrabalho — novos ativos, novas tabelas ou mais usuários não devem exigir reescrever a estrutura.

## Como rodar

```bash
# 1. Criar e ativar o ambiente (uma vez)
conda env create -f environment.yml
conda activate robo_advisor

# 2. Criar o banco e popular os dados de teste (uma vez)
python src/banco.py

# 3. Rodar o fluxo completo (questionário → perfil → carteira)
python src/main.py
```

> Rode os comandos a partir da raiz do projeto (a pasta `Robo_Advisor/`).

## Estrutura

| Arquivo / pasta | Papel |
|---|---|
| `src/main.py` | Orquestra o fluxo completo |
| `src/questionario_v1.py` | Coleta as respostas do investidor |
| `src/suitability.py` | Calcula o perfil (Conservador / Moderado / Agressivo) |
| `src/alocacao_teste.py` | Monta a carteira a partir do perfil |
| `src/banco.py` | Camada de banco de dados (SQLite) |
| `config/allocation.yaml` | Percentuais de alocação por perfil (editável sem tocar no código) |
| `docs/` | Material de referência |

## Stack

Python · SQLite · pandas · pyyaml

Referência principal: *"Build a Robo-Advisor from Scratch"* — Rob Reider
