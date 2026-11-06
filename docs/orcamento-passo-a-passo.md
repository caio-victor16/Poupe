# Correção 10b — orçamento no servidor

## 1. O problema

`orcamento.html` guardava os limites só no navegador e calculava o gasto
somando **todo o histórico** do cache de gastos, comparando pelo **nome**
da categoria. O formulário oferecia "Estudos" (o banco tem "educação") e
não oferecia moradia, energia nem internet. O backend já tinha a tabela
`orcamento_categoria` e as rotas `/orcamentos`, que calculam o gasto do mês
atual por **id** de categoria, mas a tela não as usava.

## 2. O que mudou

### `frontend/api.js`
- `OrcamentoAPI`: `statusDoMes`, `definir` (cria ou substitui o limite da
  categoria), `excluir`, `verificar`.
- `DadosLocais.sincronizar()` também regrava `poupe_orcamentos_u<ID>`
  (orçamentos do servidor, com `gasto_mes`, `percentual`, `situacao`, e os
  itens que ainda só existem no navegador).

### `frontend/orcamento.html`
- Categorias carregadas do banco; o limite é salvo pelo id da categoria.
- Gasto do mês e percentual vêm do servidor (só o mês atual).
- Limites antigos do navegador migram para o servidor ao abrir a tela.
  "Estudos" vira "Educação". Limite sem categoria correspondente fica
  num quadro "Limites salvos só neste navegador", com botão de excluir.
  Cada item só sai do navegador depois que o servidor confirma.
- Ao abrir, chama `POST /orcamentos/usuario/<id>/verificar`: categorias em
  80% ou mais viram alertas na tela de Alertas, no máximo um por categoria e
  situação por dia (regra do backend).
- Valida limite maior que zero; exclusão pede confirmação.

### `frontend/score.html`
- Usa o `gasto_mes` do servidor quando o orçamento vem dele (antes somava
  todo o histórico).

## 3. Limites

- A tabela não tem índice único (usuário, categoria): dois cliques
  simultâneos em abas diferentes poderiam criar dois limites para a mesma
  categoria.
- "Mês atual" é o do servidor MySQL.
- O alerta de orçamento só é gerado quando a tela de orçamento é aberta.

## 4. Testes

- `tests/test_recorrencias.cjs` (+4): sincronização dos orçamentos
  preservando pendentes, migração por id com o caso "Estudos", tela usando
  o servidor, score usando o gasto do mês.
- `tests/e2e/e2e_orcamento.py`: navegador real + Flask + MySQL descartável.
  Gasto do mês passado ignorado, migração, redefinir sem duplicar, alertas
  sem repetição, exclusão (servidor e local), score. 14/14 aprovadas.
