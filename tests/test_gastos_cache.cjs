// Executar: node --test tests/test_gastos_cache.cjs
// Item 7: gastos.html grava o cache na mesma chave por usuário que as outras telas leem.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const root = path.join(__dirname, '..', 'frontend');
const ler = (arquivo) => fs.readFileSync(path.join(root, arquivo), 'utf8');
const api = ler('api.js');
const gastosHtml = ler('gastos.html');

function trecho(fonte, inicio, fim) {
  const a = fonte.indexOf(inicio);
  const b = fonte.indexOf(fim, a);
  assert.ok(a >= 0 && b > a, `trecho não encontrado: ${inicio}`);
  return fonte.slice(a, b);
}

function storageFalso(inicial = {}) {
  const dados = new Map(Object.entries(inicial));
  return {
    dados,
    getItem: (k) => (dados.has(k) ? dados.get(k) : null),
    setItem: (k, v) => dados.set(k, String(v)),
    removeItem: (k) => dados.delete(k),
  };
}

// Executa o carregarGastos() real da página com a API simulada.
async function carregar(localStorage, resposta) {
  const contexto = vm.createContext({
    localStorage,
    console: { error() {} },
    alert() {},
    usuarioId: localStorage.getItem('usuarioId'),
    gastosCache: [],
    categoriaPorId: { 1: 'alimentação', 4: 'lazer' },
    GastoAPI: {
      listarPorUsuario: async () => {
        if (resposta instanceof Error) throw resposta;
        return resposta;
      },
    },
  });
  vm.runInContext(trecho(api, 'function chaveUsuario', 'function atualizarTema'), contexto);
  vm.runInContext(trecho(api, 'function capitalizar', 'function recorrenciaParaCache'), contexto);
  const bloco = trecho(gastosHtml, 'async function carregarGastos', 'DATA DE HOJE');
  vm.runInContext(bloco.slice(0, bloco.lastIndexOf('/*')), contexto);
  await vm.runInContext('carregarGastos()', contexto);
  return contexto;
}

const DO_SERVIDOR = [
  { id_gasto: 7, descricao: 'Mercado', valor: '120.50', data: '2026-11-01', id_categoria: 1 },
  { id_gasto: 8, descricao: null, valor: '30.00', data: '2026-11-02', id_categoria: 4 },
];

test('gastos.html grava na chave por usuário e remove a chave global antiga', async () => {
  const ls = storageFalso({ usuarioId: '5', poupe_gastos: '[{"valor":999,"descricao":"de outra conta"}]' });
  await carregar(ls, DO_SERVIDOR);
  const salvo = JSON.parse(ls.getItem('poupe_gastos_u5'));
  assert.equal(salvo.length, 2);
  assert.equal(salvo[0].categoria, 'Alimentação');
  assert.equal(salvo[1].descricao, '');   // desperdicio.html chama .toLowerCase()
  assert.equal(ls.getItem('poupe_gastos'), null);
});

test('falha no servidor limpa só o cache do usuário atual', async () => {
  const ls = storageFalso({ usuarioId: '5', poupe_gastos_u5: '[{"valor":1}]', poupe_gastos_u9: '[{"valor":2}]' });
  await carregar(ls, new Error('offline'));
  assert.equal(ls.getItem('poupe_gastos_u5'), '[]');
  assert.equal(ls.getItem('poupe_gastos_u9'), '[{"valor":2}]');
});

test('as telas que leem gastos usam exatamente a chave gravada', async () => {
  const ls = storageFalso({ usuarioId: '5' });
  await carregar(ls, DO_SERVIDOR);
  // orcamento.html deixou de ler gastos no navegador (item 10b: o servidor calcula).
  const leitores = ['score.html', 'cofrinho.html', 'desperdicio.html'];
  for (const arquivo of leitores) {
    const fonte = ler(arquivo);
    assert.ok(fonte.includes('localStorage.getItem(chaveUsuario("poupe_gastos"))'), arquivo);
  }
  // Simula a leitura de orcamento.html/score.html: soma por categoria.
  const contexto = vm.createContext({ localStorage: ls });
  vm.runInContext(trecho(api, 'function chaveUsuario', 'function atualizarTema'), contexto);
  const lidos = vm.runInContext('JSON.parse(localStorage.getItem(chaveUsuario("poupe_gastos")) || "[]")', contexto);
  const lazer = lidos.filter((g) => g.categoria === 'Lazer').reduce((t, g) => t + Number(g.valor), 0);
  assert.equal(lazer, 30);
});

test('nenhuma página lê ou grava "poupe_gastos" sem chaveUsuario', () => {
  for (const arquivo of fs.readdirSync(root).filter((f) => f.endsWith('.html') || f.endsWith('.js'))) {
    const fonte = ler(arquivo);
    for (const m of fonte.matchAll(/localStorage\.(getItem|setItem)\(\s*["']poupe_gastos["']/g)) {
      assert.fail(`${arquivo}: ${m[0]}`);
    }
  }
});
