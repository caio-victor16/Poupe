# Correção 7 — mesma chave de gastos em todas as telas

## 1. O problema

`gastos.html` buscava os gastos na API e guardava uma cópia no navegador em
`localStorage["poupe_gastos"]`. Orçamento, score, cofrinho e desperdício
liam `chaveUsuario("poupe_gastos")`, ou seja, `poupe_gastos_u<ID>`. As
chaves nunca coincidiam: essas telas sempre viam zero gastos.

A chave global também era compartilhada entre contas no mesmo navegador:
a lista de um usuário ficava lá depois do logout.

## 2. O que mudou (`frontend/gastos.html`, `carregarGastos`)

- Grava em `chaveUsuario("poupe_gastos")`, a mesma chave dos leitores.
- Em falha da API, zera só o cache do usuário atual.
- Remove a chave antiga `poupe_gastos` sempre que carrega.
- `descricao` nula vira `""`: `desperdicio.html` chama `.toLowerCase()`
  nela e quebraria com gastos sem descrição.

## 3. Limites

- O cache só é atualizado quando a tela de gastos é aberta. Quem for
  direto ao orçamento ou ao score vê os dados da última visita a gastos
  (ou nada). Buscar da API nessas telas faz parte do item 10.
- Os leitores somam todos os gastos do cache, sem filtrar o mês.
- O orçamento oferece "Estudos", mas a categoria do banco é "educação";
  "Moradia", "Energia" e "Internet" não existem no orçamento. Essas
  categorias não batem (validação de dados, item 12).
- `caixa (1).html` ainda usa chaves sem usuário (`poupe_contas`); fica
  para o item 8.

## 4. Testes

`tests/test_gastos_cache.cjs` executa o `carregarGastos()` real da página
com API simulada e confere: chave por usuário, remoção da chave antiga,
falha sem afetar outra conta, leitura pelas telas consumidoras e ausência
de `"poupe_gastos"` sem `chaveUsuario` em qualquer página. Contra o código
antigo, os 4 testes falham.

```text
node --test tests/test_gastos_cache.cjs tests/test_xss.cjs
```
