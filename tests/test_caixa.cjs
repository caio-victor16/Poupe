// Executar: node --test tests/test_caixa.cjs
// Item 8: radar do Caixa sem ReferenceError, lendo gastos (não contas) do mês atual.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const root = path.join(__dirname, '..', 'frontend');
const ler = (arquivo) => fs.readFileSync(path.join(root, arquivo), 'utf8');
const api = ler('api.js');

function trecho(fonte, inicio, fim) {
  const a = fonte.indexOf(inicio);
  const b = fonte.indexOf(fim, a);
  assert.ok(a >= 0 && b > a, `trecho não encontrado: ${inicio}`);
  return fonte.slice(a, b);
}

// Hoje fixo: 10/11/2026 (mês com 30 dias -> 20 dias restantes).
class DataFixa extends Date {
  constructor(...args) {
    if (args.length) super(...args);
    else super(2026, 10, 10, 12, 0, 0);
  }
}

function radar(itens, saldoTotal) {
  const dados = new Map(Object.entries({ usuarioId: '5', ...itens }));
  const elementos = {};
  const contexto = vm.createContext({
    Date: DataFixa,
    localStorage: { getItem: (k) => (dados.has(k) ? dados.get(k) : null) },
    document: { getElementById: (id) => (elementos[id] ??= { textContent: '' }) },
  });
  vm.runInContext(trecho(api, 'function chaveUsuario', 'function atualizarTema'), contexto);
  vm.runInContext(trecho(ler('caixa.html'), 'function calcularRadar', 'function renderizar'), contexto);
  contexto.calcularRadar(saldoTotal);
  return Object.fromEntries(Object.entries(elementos).map(([k, v]) => [k, v.textContent.replace(/\s/g, ' ')]));
}

test('caixa.html não usa mais llocalStorage nem lê contas como gastos', () => {
  const fonte = trecho(ler('caixa.html'), 'function calcularRadar', 'function renderizar');
  assert.ok(!fonte.includes('llocalStorage'));
  assert.ok(!fonte.includes('"poupe_contas"'));
  assert.ok(fonte.includes('chaveUsuario("poupe_gastos")'));
});

test('radar funciona sem dados (antes lançava ReferenceError)', () => {
  const r = radar({}, 0);
  assert.equal(r.radarSaldoLivre, 'R$ 0,00');
  assert.equal(r.radarDiasDura, '20 dias');
  assert.equal(r.radarGastoDiario, 'R$ 0,00/dia');
});

test('radar usa só gastos do mês atual e ignora saldos das contas', () => {
  const r = radar({
    poupe_gastos_u5: JSON.stringify([
      { valor: '100.00', data: '2026-11-02' },
      { valor: 50, data: '2026-11-09' },
      { valor: 9999, data: '2026-10-31' },   // mês anterior: fora
      { valor: 7777, data: '2025-11-05' },   // mesmo mês, outro ano: fora
    ]),
    poupe_gastos_u9: JSON.stringify([{ valor: 5000, data: '2026-11-01' }]), // outra conta
    poupe_contas_u5: JSON.stringify([{ saldo: 3000 }]),                     // não é gasto
    poupe_recorrencias_u5: JSON.stringify([
      { tipo: 'Gasto Fixo', dia: 15, valor: 200 },  // ainda vence este mês
      { tipo: 'Gasto Fixo', dia: 5, valor: 900 },   // já venceu
      { tipo: 'Receita Fixa', dia: 20, valor: 800 },
    ]),
  }, 3000);
  // saldo livre = 3000 - 200 = 2800; média diária = 150 / 10 = 15
  assert.equal(r.radarSaldoLivre, 'R$ 2.800,00');
  assert.equal(r.radarDiasDura, '186 dias');          // floor(2800 / 15)
  assert.equal(r.radarGastoDiario, 'R$ 140,00/dia');  // 2800 / 20 dias restantes
});

test('cópia antiga caixa (1).html usa chaves por usuário', () => {
  const fonte = ler('caixa (1).html');
  assert.ok(!/localStorage\.(get|set)Item\(\s*["']poupe_contas["']/.test(fonte));
  assert.equal((fonte.match(/chaveUsuario\("poupe_contas"\)/g) || []).length, 2);
});
