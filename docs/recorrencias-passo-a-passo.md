# Correção 10a — recorrências no servidor e cópias locais atualizadas

O item 10 foi dividido. Esta etapa (10a) cobre recorrências de gasto e as
telas que calculam com gastos. Orçamento, receitas, contas, metas e
cofrinhos no servidor ficam para as próximas etapas.

## 1. O problema

- `recorrencia.html` salvava tudo só no `localStorage`. O backend já tinha
  a tabela `recorrencia_gasto`, as rotas `/recorrencias` e o processamento
  que gera os gastos vencidos, mas nada disso era usado.
- Orçamento, score, cofrinho, desperdício e caixa calculam com uma cópia
  local dos gastos que só era atualizada ao abrir a tela de gastos.

## 2. O que mudou

### `frontend/api.js`
- `RecorrenciaAPI`: listar, criar, excluir e processar.
- `gastoParaCache` / `recorrenciaParaCache`: formato único das cópias
  locais (o de recorrência é o que caixa e score já liam: `tipo`, `dia`,
  `valor`).
- `DadosLocais.sincronizar()`: processa as recorrências vencidas, depois
  regrava `poupe_gastos_u<ID>` e `poupe_recorrencias_u<ID>` (recorrências
  ativas do servidor + itens que só existem no navegador). Em falha, mantém
  a cópia anterior.

### `frontend/recorrencia.html`
- **Gasto fixo** → servidor, `frequencia: "mensal"`, com categoria
  (campo novo) e `proxima_data` = próxima ocorrência do dia escolhido
  (hoje conta; dia 31 em mês de 30 vira 30).
- **Receita fixa** → continua no navegador (não há backend de receitas),
  marcada como "(neste navegador)".
- Gastos fixos antigos que estavam só no navegador são enviados ao servidor
  na categoria "Outros" ao abrir a tela; cada um só sai do navegador depois
  que o servidor confirma. Itens com dia ou valor inválido ficam locais.
- Excluir gasto fixo pede confirmação; gastos já gerados continuam.
- Validação: valor > 0 e dia inteiro 1–31; botão desativado ao salvar.

### Demais telas
- `gastos.html`: processa recorrências antes de listar, então o gasto
  gerado aparece na hora.
- `orcamento`, `score`, `cofrinho`, `desperdicio`, `caixa`: chamam
  `DadosLocais.sincronizar()` antes de ler as cópias locais.

## 3. Limites

- Toda tela leitora faz algumas requisições ao abrir (processar + listas).
- O backend grava `dia_mes` a partir da `proxima_data`: recorrência criada
  para "dia 31" em novembro passa a ser "dia 30" nos meses seguintes.
- Só frequência mensal pela interface (o backend aceita semanal e anual).
- Score conta como "atrasado" o gasto fixo com dia anterior a hoje, mesmo
  que o gasto já tenha sido gerado (lógica antiga do score, não alterada).
- Receitas fixas não geram receitas automaticamente.
- Orçamento continua só no navegador, embora o backend tenha
  `orcamento_categoria` (próxima etapa).

## 4. Testes

- `tests/test_recorrencias.cjs` (8): `proximaData` (fim de mês, virada de
  ano), sincronização (ordem, formato, preservação de itens locais,
  falha mantém cópia), migração (só remove o que o servidor aceitou),
  ordem "sincroniza antes de ler" nas 5 telas. Falham todos no código antigo.
- `tests/e2e/e2e_recorrencias.py`: navegador real + Flask + MySQL
  descartável. Cadastro/login, migração, criação, exclusão, geração do
  gasto, recarga sem duplicar, telas leitoras sem erro de JavaScript.
  Executado com Chrome + MariaDB 10.11: 14/14 verificações aprovadas.
