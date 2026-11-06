# Correção 10c (parte 2) — contas, metas, cofrinhos e receitas fixas no servidor

## ⚠️ Ação necessária num banco já instalado

```text
python setup_db.py --atualizar
```

Cria as tabelas `receita_recorrente`, `conta`, `meta` e `cofrinho` (e
`receita`, se ainda não rodou na parte 1). Não altera tabelas existentes
nem apaga dados. Sem isso o servidor não sobe.

## 1. Problemas

- Contas do caixa, metas, cofrinhos e receitas fixas existiam só no
  navegador.
- **Metas quebradas:** `metas.html` carrega o `api.js` com `defer`, mas o
  script da página chamava `chaveUsuario()` antes de ele existir. A tela
  dava `ReferenceError` ao abrir e não mostrava nada (confirmado no Chrome).
- **Metas sumiam:** salvar e excluir gravavam em `poupePlus_goals`, sem o ID
  do usuário, e a leitura usava a chave com ID.
- Cofrinho: o aporte fazia "ler, somar e gravar" no navegador; duas abas
  podiam perder um aporte.

## 2. Backend

- `backend/crud.py`: validadores (`texto`, `escolha`, `dinheiro`, `inteiro`)
  e `CrudSimples`, que monta as 4 rotas padrão por recurso (criar, listar
  por usuário, alterar parcial, excluir). Usado por contas, metas e
  cofrinhos; receitas fixas usam criar/alterar próprios.
- `backend/controllers/financas_controller.py`:
  - `/contas`: nome (até 100), tipo (Corrente, Poupança, Dinheiro Físico,
    Investimentos), saldo (pode ser negativo).
  - `/metas`: título, `valor_alvo` > 0, `valor_guardado` ≥ 0.
  - `/cofrinhos`: idem + `prazo_meses` de 1 a 600;
    `POST /cofrinhos/<id>/aportar` soma no próprio banco
    (`UPDATE ... valor_guardado = valor_guardado + x`).
  - `/receitas-recorrentes`: descrição, categoria de receita, valor > 0,
    `dia_mes` 1–31. `proxima_data` é calculada pelo servidor;
    `POST .../usuario/<id>/processar` gera as receitas vencidas e avança a
    data, sem duplicar. Dia 31 vira o último dia de meses curtos e volta a
    31 nos meses longos (o `dia_mes` original é mantido).
- `backend/auth.py`: os 4 recursos entram em CRIACAO, RECURSOS e
  POR_USUARIO. O teste genérico de propriedade já cobre todos.
- `poupe.sql`: 4 tabelas com chave estrangeira em cascata.

## 3. Frontend

- `api.js`: `ContaAPI`, `MetaAPI`, `CofrinhoAPI` (com `aportar`),
  `ReceitaRecorrenteAPI`; `migrarItensLocais()` e `sincronizarCopia()`
  genéricos. As cópias locais mantêm o formato antigo de cada tela, então
  a exibição não mudou. `DadosLocais.sincronizar()` processa gastos e
  receitas fixas, e o cache de recorrências traz as duas.
- `caixa.html`, `cofrinho.html`, `metas.html`: criam, excluem e aportam no
  servidor; migram os dados antigos do navegador ao abrir (inválidos
  ficam marcados como locais).
- `metas.html`: script reescrito para não chamar o `api.js` antes da hora;
  botões sem `onclick` com índice.
- `recorrencia.html`: receita fixa vai para o servidor com categoria de
  receita (campo novo); receitas fixas antigas migram na categoria "Outros".

## 4. Limites

- Metas e cofrinhos continuam sendo coisas separadas (como já eram nas telas).
- O saldo das contas não é atualizado automaticamente por gastos e receitas.
- As telas não têm botão de editar; a API aceita `PUT`.
- Receitas fixas só mensais.

## 5. Testes

- `tests/test_financas.py` (7): CRUD e validação dos 4 recursos, aporte,
  `_primeira_data`, geração de receitas (atraso de 3 meses, fim de mês,
  idempotência, inativa) e isolamento entre usuários.
- `tests/test_auth.py`: o teste genérico passou a cobrir os 4 recursos.
- `tests/test_recorrencias.cjs` (+6): processamento duplo, formatos de cache,
  migração genérica, sincronização, `metas.html` sem `api.js`, telas
  gravando no servidor. Os 6 falham na versão anterior.
- E2E: `tests/e2e/e2e_financas.py` 17/17; os outros 3 continuam passando
  (recorrências, agora 17/17, atualizado para receita fixa no servidor).
- MariaDB: banco da parte 1 com dados → `--atualizar` criou as 4 tabelas,
  dados intactos.
