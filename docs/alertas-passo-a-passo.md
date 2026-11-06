# Correção 14 — alerta de limite sem repetição

## ⚠️ Ação necessária num banco já instalado

```text
python setup_db.py --atualizar
```

A correção está numa procedure. O `--atualizar` recria as procedures sem
tocar em tabelas nem dados.

## 1. O problema

`gastos.html` chama `POST /alertas/usuario/<id>/gerar-limite` a cada gasto
cadastrado acima de 80% do limite. A procedure `sp_gerar_alerta_limite`
inseria um alerta novo **toda vez**: com 10 gastos no mês acima de 80%,
o usuário recebia 10 alertas iguais.

Reproduzido em MariaDB com a procedure anterior: 5 chamadas → 5 alertas.

## 2. O que mudou (`database/mysql/poupe.sql`)

- No máximo **um alerta de cada situação por usuário e por mês**:
  "você está próximo do seu limite" (≥ 80%) e "seu limite foi
  ultrapassado" (≥ 100%). O limite é mensal, então no mês seguinte volta a
  alertar.
- A inserção virou um único `INSERT ... SELECT ... WHERE NOT EXISTS`
  (alerta igual no mês atual).
- `GET_LOCK` por usuário em volta da inserção: chamadas simultâneas não
  criam dois alertas.

## 3. Limites

- Se o usuário excluir o alerta do mês, a próxima chamada cria outro
  (comportamento intencional: ele continua acima do limite).
- O "mês" é o do servidor MySQL, como nas outras procedures do limite.
- Os alertas de **orçamento** por categoria já evitavam repetição no mesmo
  dia (regra do backend, item 10b) e não mudaram.

## 4. Validação

- MariaDB (banco da versão anterior + `--atualizar`): 5 chamadas a 85% → 1
  alerta; acima de 100% → +1 (ultrapassado), 3 chamadas não duplicam; mês
  seguinte → novo alerta; abaixo de 80% → nenhum; **20 chamadas
  simultâneas → 1 alerta**.
- `tests/test_setup_db.py` (+1): a procedure tem uma única inserção, com
  `NOT EXISTS` e trava.
- `tests/e2e/e2e_alertas.py` 7/7: gastos cadastrados pela tela de gastos
  (50% → 85% → 3 gastos a mais → 108% → mais um) e tela de alertas com um de cada.
- Regressão: os 7 E2E em sequência no mesmo banco (107 verificações).
