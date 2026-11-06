# Correção 8 — radar do Caixa

## 1. O problema (`frontend/caixa.html`, `calcularRadar`)

- `llocalStorage` (dois "l") não existe: lançava `ReferenceError` toda vez.
  Como `renderizar()` chama o radar antes de ativar os ícones e os botões
  de excluir, a tela ficava com o radar vazio, sem ícones e com os botões
  de exclusão sem efeito.
- A variável `gastos` lia `poupe_contas` (as contas e seus saldos), não os
  gastos. A "média diária de gastos" era calculada sobre os saldos.
- Mesmo com a chave certa, somaria todo o histórico, mas a conta divide
  pelo dia do mês (é uma média do mês atual).

## 2. O que mudou

- `localStorage` corrigido.
- `gastos` lê `chaveUsuario("poupe_gastos")` (o cache da tela de gastos,
  item 7) e filtra só o mês e ano atuais pelo campo `data` (`AAAA-MM-DD`).
- `caixa (1).html`: cópia antiga, sem radar e sem link em nenhuma página,
  mas acessível pelo Flask. Usava `poupe_contas` sem usuário (contas de uma
  conta visíveis para outra no mesmo navegador). Passou a usar
  `chaveUsuario`. Recomendação: apagar o arquivo.

## 3. Limites

- Os gastos vêm do cache que só atualiza ao abrir a tela de gastos
  (item 10).
- Contas e recorrências continuam só no navegador (item 10).
- "Boletos pendentes" considera recorrências do tipo "Gasto Fixo" com dia
  maior ou igual a hoje; não sabe se a recorrência já foi paga.

## 4. Testes

`tests/test_caixa.cjs` executa o `calcularRadar()` real com data fixa
(10/11/2026) e confere: sem erro com dados vazios, filtro do mês, gastos
de outra conta e saldos de contas ignorados, cálculos de saldo livre, dias
e limite diário. Contra o código antigo, os 4 testes falham.

```text
node --test tests/test_xss.cjs tests/test_gastos_cache.cjs tests/test_caixa.cjs
```
