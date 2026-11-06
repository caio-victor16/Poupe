# Correção 9 — limite de gastos só do mês atual

## 1. O problema

`sp_verificar_limite_gastos` (rota `GET /gastos/usuario/<id>/limite`) e
`sp_gerar_alerta_limite` (rota `POST /alertas/usuario/<id>/gerar-limite`)
somavam **todos** os gastos do usuário desde o cadastro. O limite é mensal:
depois de alguns meses de uso, todo usuário aparecia como "limite
excedido" e recebia alerta, mesmo gastando pouco no mês. Score e orçamento
do backend já usavam só o mês.

Reproduzido em MariaDB com o SQL antigo: limite R$ 1.000, R$ 900 no mês
passado, R$ 300 neste mês e R$ 500 com data no mês que vem → total R$ 1.700,
170%, `limite_excedido`, alerta criado.

## 2. O que mudou (`database/mysql/poupe.sql`)

- As duas procedures filtram `data >= primeiro dia do mês atual` e
  `data < primeiro dia do mês seguinte`, o mesmo critério do
  `score_repository.py`. Gastos com data futura (mês seguinte) não contam.
- No `sp_verificar_limite_gastos` o filtro fica no `LEFT JOIN`: usuário
  sem gastos no mês continua aparecendo com total 0.
- `nullif(u.limite_gastos, 0)`: limite zero deixa o percentual `NULL` em vez
  de depender da configuração de divisão por zero do servidor.

Mesmo cenário depois da correção: R$ 300, 30%, `dentro_do_limite`, nenhum
alerta. Com mais R$ 550 hoje: R$ 850, 85%, `proximo_do_limite`.

## 3. Atualizando um banco já instalado

O instalador não altera bancos completos (item 6), então as procedures
antigas continuam no seu MySQL até você rodar:

```text
python setup_db.py --atualizar-procedures
```

Esse comando só funciona em banco com todas as tabelas do Poupe+, apaga e
recria apenas as 7 procedures do `poupe.sql` e não altera tabelas nem dados.
Testado em MariaDB 10.11: 5 gastos e 2 usuários intactos depois.

## 4. Limites

- "Mês atual" usa a data do servidor MySQL (`curdate()`), não o fuso do
  usuário. Perto da meia-noite do último dia do mês pode haver diferença.
- Limite zero: `situacao` fica `limite_excedido` (0 ≥ 0). O cadastro já
  recusa limite zero hoje; a validação completa é o item 12.
- Alertas repetidos a cada chamada continuam (item 14).
- Os cálculos feitos no navegador (orçamento, score em `score.html`) somam
  o cache local inteiro; isso é do item 10.

## 5. Testes

- `tests/test_setup_db.py`: filtro mensal presente nas duas procedures;
  `--atualizar-procedures` só executa `DROP/CREATE PROCEDURE` e recusa
  banco ausente ou incompleto.
- Cenários acima executados em MariaDB 10.11 descartável.
