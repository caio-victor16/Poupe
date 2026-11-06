# Correção 11 — painel inicial com dados reais

## 1. O problema

`inicio.html` tinha toda a estrutura (resumo, últimos gastos, rosca por
categoria, evolução), mas nenhum script a preenchia: tudo ficava em
R$ 0,00, sem gráficos e sem lista. O mês estava fixo em "Agosto de 2026" e
o avatar fixo em "D".

## 2. O que mudou (`frontend/inicio.html`)

Funções puras de cálculo (testáveis sem navegador):

| Função | O que faz |
|---|---|
| `resumoDoMes` | receitas, gastos e saldo do mês escolhido (soma em centavos) |
| `gastosPorCategoria` | total e % por categoria, maior primeiro |
| `evolucaoDiaria` | gasto acumulado por dia; no mês atual a linha para em hoje |
| `progressoDoMes` | % do mês decorrido (passado 100%, futuro 0%) |
| `ultimosGastos` | 5 gastos mais recentes do mês |

Interface:
- Dados das cópias locais de gastos e receitas, atualizadas do servidor por
  `DadosLocais.sincronizar()` (que também processa recorrências vencidas).
  Mostra a cópia na hora e atualiza quando o servidor responde.
- Setas de mês anterior/próximo; os gráficos antigos são destruídos antes
  de redesenhar.
- Cumprimento e avatar com o nome do usuário (via `textContent`).
- Sino mostra quantos alertas não lidos existem e leva à tela de Alertas.
- Dados externos no HTML passam por `textoHTML`.
- Sem Chart.js (CDN fora do ar), números, legenda e lista continuam
  funcionando; só os gráficos não aparecem.

## 3. Limites

- O painel usa a data do navegador para "mês atual"; o backend usa a do
  servidor MySQL. Em fusos diferentes, perto da virada do mês, podem divergir.
- Categorias com nomes iguais e caixa diferente contam separado (os nomes
  vêm do banco, então isso só ocorre se o banco tiver duplicatas).
- Saldo disponível = receitas − gastos do mês; não usa o saldo das contas.

## 4. Testes

- `tests/test_inicio.cjs` (6): resumo, categorias, evolução (mês de 30
  dias, fevereiro bissexto, corte em hoje), progresso, últimos gastos,
  ausência de valores fixos e escape.
- `tests/e2e/e2e_inicio.py`: 22/22 no Chrome com MariaDB descartável —
  números, legenda, lista com HTML escapado, nome, contador de alertas,
  dados enviados aos gráficos, navegação entre meses, estado vazio.
- Print com Chart.js e lucide reais: `painel-inicial.png` (entregue na conversa).
