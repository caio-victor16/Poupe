// Executar: node --test tests/test_inicio.cjs
// Item 11: cálculos do painel inicial (funções reais de inicio.html).
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const fonte = fs.readFileSync(path.join(__dirname, '..', 'frontend', 'inicio.html'), 'utf8');
const inicio = fonte.indexOf('const NOMES_MESES');
const fim = fonte.indexOf("document.addEventListener('DOMContentLoaded'", inicio);
assert.ok(inicio > 0 && fim > inicio);
const ctx = vm.createContext({});
vm.runInContext(fonte.slice(inicio, fim), ctx);
const j = (x) => JSON.parse(JSON.stringify(x));

const GASTOS = [
  { id: 1, descricao: 'Mercado', valor: '120.10', data: '2026-11-02', categoria: 'Alimentação' },
  { id: 2, descricao: 'Uber', valor: 30.2, data: '2026-11-02', categoria: 'Transporte' },
  { id: 3, descricao: 'Feira', valor: 49.7, data: '2026-11-05', categoria: 'Alimentação' },
  { id: 4, descricao: 'Antigo', valor: 999, data: '2026-10-31', categoria: 'Lazer' },
  { id: 5, descricao: 'Ano passado', valor: 777, data: '2025-11-05', categoria: 'Lazer' },
];
const RECEITAS = [
  { description: 'Salário', amount: 5000, date: '2026-11-05' },
  { description: 'Freela', amount: '0.1', date: '2026-11-20' },
  { description: 'Outubro', amount: 4000, date: '2026-10-05' },
];

test('resumo do mês: só o mês escolhido, somas sem erro de centavos', () => {
  assert.deepEqual(j(ctx.resumoDoMes(GASTOS, RECEITAS, 2026, 10)), { receitas: 5000.1, gastos: 200, saldo: 4800.1 });
  assert.deepEqual(j(ctx.resumoDoMes(GASTOS, RECEITAS, 2026, 9)), { receitas: 4000, gastos: 999, saldo: 3001 });
  assert.deepEqual(j(ctx.resumoDoMes([], [], 2026, 10)), { receitas: 0, gastos: 0, saldo: 0 });
  assert.equal(ctx.resumoDoMes([{ valor: 10, data: '2026-11-01' }], [], 2026, 10).saldo, -10);
  assert.equal(ctx.somar([{ v: 0.1 }, { v: 0.2 }], 'v'), 0.3);             // 0.1 + 0.2 sem 0.30000000000000004
});

test('gastos por categoria: totais, percentuais e ordem', () => {
  const doMes = ctx.doMes(GASTOS, 'data', 2026, 10);
  assert.deepEqual(j(ctx.gastosPorCategoria(doMes)), [
    { categoria: 'Alimentação', total: 169.8, percentual: 85 },
    { categoria: 'Transporte', total: 30.2, percentual: 15 },
  ]);
  assert.deepEqual(j(ctx.gastosPorCategoria([])), []);
  assert.equal(ctx.gastosPorCategoria([{ valor: 5 }])[0].categoria, 'Outros');
});

test('evolução diária acumulada cobre todos os dias do mês', () => {
  const ev = ctx.evolucaoDiaria(ctx.doMes(GASTOS, 'data', 2026, 10), 2026, 10);
  assert.equal(ev.rotulos.length, 30);                 // novembro
  assert.equal(ev.valores[0], 0);
  assert.equal(ev.valores[1], 150.3);                  // dia 2: 120,10 + 30,20
  assert.equal(ev.valores[4], 200);                    // dia 5: + 49,70
  assert.equal(ev.valores[29], 200);
  assert.equal(ctx.evolucaoDiaria([], 2028, 1).rotulos.length, 29);   // fevereiro bissexto
  const ateHoje = ctx.evolucaoDiaria(ctx.doMes(GASTOS, 'data', 2026, 10), 2026, 10, 5);
  assert.equal(ateHoje.valores[4], 200);                              // dia 5 = hoje
  assert.equal(ateHoje.valores[5], null);                             // depois de hoje: sem linha
});

test('progresso do mês: atual proporcional, passado 100, futuro 0', () => {
  const hoje = new Date(2026, 10, 15);
  assert.equal(ctx.progressoDoMes(hoje, 2026, 10), 50);
  assert.equal(ctx.progressoDoMes(hoje, 2026, 9), 100);
  assert.equal(ctx.progressoDoMes(hoje, 2025, 11), 100);
  assert.equal(ctx.progressoDoMes(hoje, 2026, 11), 0);
  assert.equal(ctx.progressoDoMes(hoje, 2027, 0), 0);
});

test('últimos gastos: mais recentes primeiro, desempate por id, limite', () => {
  const doMes = ctx.doMes(GASTOS, 'data', 2026, 10);
  assert.deepEqual(j(ctx.ultimosGastos(doMes).map(g => g.id)), [3, 2, 1]);
  assert.equal(ctx.ultimosGastos(doMes, 2).length, 2);
});

test('sem valores fixos no HTML e dados externos escapados', () => {
  assert.ok(!fonte.includes('>Agosto de 2026<'));
  assert.ok(!fonte.includes('<div class="avatar-circle">D</div>'));
  for (const trecho of ['${textoHTML(c.categoria)}', "${textoHTML(g.descricao || g.categoria || 'Gasto')}",
                        "${textoHTML(g.categoria || 'Outros')}"]) {
    assert.ok(fonte.includes(trecho), trecho);
  }
  assert.ok(fonte.includes("document.querySelector('.user-greeting h1').textContent"));   // nome via textContent
});
