# Correção 10c (parte 1) — receitas no servidor

## ⚠️ Ação necessária num banco já instalado

Esta etapa cria a tabela `receita`. Um banco de versão anterior passa a
ser recusado pelo instalador ("versão anterior do Poupe+") e o servidor
não sobe até você rodar uma vez:

```text
python setup_db.py --atualizar
```

Ele cria só as tabelas que faltam (hoje, `receita`) e recria as
procedures. Não altera tabelas existentes nem apaga dados.

## 1. Problemas

- Receitas existiam só no navegador (`poupePlus_incomes_u<ID>`), sem
  tabela nem rota no backend.
- **Excluir não persistia:** a exclusão gravava em `poupePlus_incomes`, sem
  o ID do usuário; ao recarregar, a receita voltava. Essa chave sem
  usuário também ficava visível para outra conta no mesmo navegador.
- A tela abria sempre em **agosto de 2026** (`new Date(2026, 7, 1)`).
- A data padrão do formulário usava `toISOString()` (UTC): depois das 21h
  no Brasil, já sugeria o dia seguinte.

## 2. Backend

- Tabela `receita` (`id_usuario`, `descricao`, `categoria`, `valor`,
  `data`), índice (`id_usuario`, `data`), apagada em cascata com o usuário.
- `backend/models/receita.py`, `services/receita_service.py`,
  `controllers/receita_controller.py`; rotas:
  `POST /receitas`, `GET /receitas/usuario/<id>`, `PUT /receitas/<id>`,
  `DELETE /receitas/<id>`.
- Validação: descrição de 1 a 255 caracteres (aparada); categoria
  Salário, Trabalho, Investimentos ou Outros (as do formulário); valor
  maior que zero, finito, até 99.999.999,99, arredondado ao centavo (meio
  centavo para cima); data `AAAA-MM-DD` válida. `PUT` aceita alteração
  parcial com a mesma validação.
- `backend/auth.py`: `receita` entra nas regras centrais. Criação usa o
  usuário da sessão; listar de outro usuário → 403; alterar ou excluir
  receita de outro usuário → 404.

## 3. Instalador (`setup_db.py --atualizar`)

- Só roda em banco que já tem a tabela `usuario` do Poupe+.
- Executa apenas os `CREATE TABLE` de tabelas ausentes, na ordem do
  `poupe.sql`, e os `INSERT` iniciais só dessas tabelas novas.
- Recria as procedures. Nada é apagado nem alterado nas tabelas existentes.
- A mensagem de banco incompleto agora sugere `--atualizar` antes do reset.

## 4. Frontend

- `api.js`: `ReceitaAPI`; `receitaParaCache` mantém o formato que score e
  relatórios leem (`description`, `category`, `amount`, `date`);
  `DadosLocais.sincronizarReceitas()` também apaga a chave sem usuário.
- `receitas.html`: salva e exclui no servidor; receitas antigas do
  navegador migram ao abrir (as inválidas ficam marcadas "(neste
  navegador)" e podem ser excluídas); abre no mês atual; data padrão no
  fuso local; valida campos; botão desativado ao salvar.
- `relatorios.html`: sincroniza receitas antes de montar o relatório.
  Score já sincroniza por `DadosLocais.sincronizar()`.

## 5. Limites

- Contas (caixa), metas, cofrinhos e receitas fixas continuam no
  navegador (próximas partes do 10c).
- A lista de categorias de receita está fixa no backend e no formulário.
- Editar receita existe na API, mas a tela não tem botão de editar.

## 6. Testes

- `tests/test_receitas.py` (6): CRUD, 17 entradas inválidas, arredondamento,
  atualização inválida não altera, isolamento entre usuários, login e CSRF.
- `tests/test_auth.py`: o teste genérico de propriedade passou a cobrir receita.
- `tests/test_setup_db.py` (+5): `--atualizar` cria só o que falta, insere
  dados iniciais só de tabela nova, não faz nada em banco completo, recusa
  banco que não é do Poupe+, recusa opções combinadas.
- `tests/test_recorrencias.cjs` (+4): sincronização, migração, `hojeISO`, tela.
- `tests/e2e/e2e_receitas.py`: 18/18 no Chrome com MariaDB descartável.
- MariaDB real: banco da versão anterior com dados → recusado com a
  mensagem certa → `--atualizar` criou `receita` (índice e chave
  estrangeira) com os dados intactos → segunda execução não criou nada.
