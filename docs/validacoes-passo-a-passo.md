# Correção 12 — validações de gastos, boletos e usuário

## 1. O problema

- **Gasto e boleto (criar):** só conferia se os campos existiam. Valor 0,
  negativo, `"abc"`, `NaN` ou `true`, categoria inexistente, data `30/02`
  ou no ano `0026` chegavam ao banco (erro do banco ou dado errado).
- **Gasto e boleto (`PUT`):** gravava qualquer coisa, sem validar. Um
  `ValueError` virava erro 500, porque o controller não o tratava.
- **Gastos por período:** as datas iam direto para a procedure;
  `inicio=ontem` virava erro do banco, e início depois do fim era aceito.
- **Cadastro:** `if not dados.get(campo)` tratava **renda 0** como
  "campo obrigatório"; e-mail sem "@" era aceito; o `PUT` do perfil não
  validava nada.
- **Tela de cadastro:** `min="0.01"` na renda barrava o zero no navegador.

Confirmado executando `tests/test_validacoes.py` no backend original: os
10 testes falham, com 38 casos inválidos aceitos.

## 2. O que mudou

- `backend/crud.py`: validadores novos `texto_opcional`, `booleano`,
  `email`, `telefone`, `id_existente(modelo)`; `data_iso` exige ano entre
  1900 e 2100.
- `gasto_service.py`: categoria existente, valor > 0 (2 casas, meio centavo
  para cima), data válida, descrição até 255 (vazia → nula), `recorrente`
  booleano, tipo e status de pagamento opcionais. O `PUT` valida tudo antes
  de alterar qualquer campo. Período: datas válidas e início ≤ fim.
- `boleto_service.py`: código de barras/linha digitável com 44 a 48 dígitos
  (espaços, pontos e hífens aceitos e removidos; grava só dígitos), valor > 0,
  vencimento válido, status `pendente`, `pago` ou `vencido`. Mesmo cuidado no `PUT`.
- `usuario_service.py`: nome até 100; e-mail válido até 150; telefone
  opcional (números, espaços, parênteses, + e -); **renda ≥ 0**; **limite > 0**
  (com mensagem clara; limite 0 faria todo gasto estourar o limite e gerar
  alerta); senha pela regra existente. O `PUT` do perfil valida antes de alterar.
- `gasto_controller.py` e `boleto_controller.py`: `ValueError` no `PUT` → 400.
- `cadastro.html`: renda aceita 0 (`min="0"`).

## 3. Decisões

- **Limite 0 continua recusado**, agora com a mensagem "deve ser maior que 0"
  em vez de "obrigatório". Renda 0 passou a ser aceita (desempregado, estudante).
- Boletos gravam só os dígitos. Nenhuma tela cria boletos hoje; a regra vale
  para a API.

## 4. Limites

- E-mail validado por formato simples (não confirma se o endereço existe).
- Contas cadastradas antes com dados inválidos não são corrigidas
  automaticamente; a validação vale ao criar e ao alterar.

## 5. Testes

- `tests/test_validacoes.py` (10): gasto (criação, normalização, 15 inválidos,
  `PUT` que não altera nada quando inválido, período), boleto (dígitos,
  9 inválidos, `PUT`), usuário (renda 0, 11 inválidos, mensagem de limite,
  perfil). Os 10 falham no backend original.
- `tests/e2e/e2e_validacoes.py` 12/12 com MariaDB: cadastro com renda 0 pela
  tela e chamadas inválidas com sessão real, conferindo que o banco não mudou.
- Regressão: os 6 E2E em sequência no mesmo banco. `e2e_recorrencias.py`
  passou a contar só os registros do próprio usuário e a usar e-mail único
  (antes dependia de banco vazio).
