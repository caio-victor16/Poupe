// Executar: node --test tests/test_recorrencias.cjs
// Item 10a: recorrências de gasto no servidor e cópias locais sincronizadas.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const root = path.join(__dirname, '..', 'frontend');
const ler = (arquivo) => fs.readFileSync(path.join(root, arquivo), 'utf8');
const api = ler('api.js');
const recorrenciaHtml = ler('recorrencia.html');

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

// Carrega o código real de api.js (helpers + DadosLocais) e de recorrencia.html.
function ambiente({ storage, servidor, Date: DataClasse = Date }) {
  const chamadas = [];
  const falhar = (nome) => servidor.falhas?.includes(nome);
  const contexto = vm.createContext({
    Date: DataClasse,
    console: { error() {} },
    localStorage: storage,
    Sessao: { obterUsuarioId: () => storage.getItem('usuarioId') },
    RecorrenciaAPI: {
      processar: async (id) => { chamadas.push(['processar', id]); if (falhar('processar')) throw new Error('x'); },
      listarPorUsuario: async (id) => { chamadas.push(['listarRec', id]); if (falhar('listarRec')) throw new Error('x'); return servidor.recorrencias; },
      criar: async (dados) => {
        chamadas.push(['criar', dados]);
        if (servidor.recusar?.(dados)) throw new Error('recusado');
        return { ...dados, id_recorrencia: 99 };
      },
    },
    GastoAPI: { listarPorUsuario: async (id) => { chamadas.push(['listarGastos', id]); if (falhar('listarGastos')) throw new Error('x'); return servidor.gastos; } },
    CategoriaAPI: { listar: async () => servidor.categorias },
    ReceitaRecorrenteAPI: {
      processar: async (id) => { chamadas.push(['processarReceitas', id]); if (falhar('processarReceitas')) throw new Error('x'); },
      listarPorUsuario: async () => { if (falhar('listarReceitasFixas')) throw new Error('x'); return servidor.receitasFixas || []; },
      criar: async (dados) => { chamadas.push(['criarReceitaFixa', dados]); if (servidor.recusar?.(dados)) throw new Error('recusado'); return dados; },
    },
    ContaAPI: {
      listarPorUsuario: async () => { if (falhar('listarContas')) throw new Error('x'); return servidor.contas || []; },
      criar: async (dados) => { chamadas.push(['criarConta', dados]); if (servidor.recusar?.(dados)) throw new Error('recusado'); return dados; },
    },
    ReceitaAPI: {
      listarPorUsuario: async (id) => { chamadas.push(['listarRec_receitas', id]); if (falhar('listarReceitas')) throw new Error('x'); return servidor.receitas || []; },
      criar: async (dados) => {
        chamadas.push(['criarReceita', dados]);
        if (servidor.recusar?.(dados)) throw new Error('recusado');
        return { ...dados, id_receita: 70 };
      },
    },
    OrcamentoAPI: {
      statusDoMes: async (id) => { chamadas.push(['statusOrc', id]); if (falhar('statusOrc')) throw new Error('x'); return servidor.orcamentos || []; },
      definir: async (dados) => {
        chamadas.push(['definirOrc', dados]);
        if (servidor.recusar?.(dados)) throw new Error('recusado');
        return { ...dados, id_orcamento: 50 };
      },
    },
  });
  vm.runInContext(trecho(api, 'function chaveUsuario', 'function atualizarTema'), contexto);
  vm.runInContext(trecho(api, 'function capitalizar', '// INTEGRAÇÃO COM AS PÁGINAS') +
    '\nglobalThis.DadosLocais = DadosLocais;', contexto);
  vm.runInContext(trecho(recorrenciaHtml, 'function proximaData', 'document.addEventListener("DOMContentLoaded"'), contexto);
  vm.runInContext(trecho(ler('receitas.html'), 'function hojeISO', "document.addEventListener('DOMContentLoaded'"), contexto);
  vm.runInContext(trecho(ler('orcamento.html'), 'const ALIASES_CATEGORIA', 'document.addEventListener("DOMContentLoaded"') +
    '\nglobalThis.ALIASES_CATEGORIA = ALIASES_CATEGORIA;', contexto);
  return { contexto, chamadas };
}

const CATEGORIAS = [{ id_categoria: 1, nome: 'alimentação' }, { id_categoria: 10, nome: 'outros' }];
const REC_SERVIDOR = [
  { id_recorrencia: 3, id_categoria: 1, valor: 39.9, descricao: 'Netflix', frequencia: 'mensal',
    proxima_data: '2026-12-05', dia_mes: 5, ativa: true },
  { id_recorrencia: 4, id_categoria: 1, valor: 10, descricao: 'Pausada', frequencia: 'mensal',
    proxima_data: '2026-12-01', dia_mes: 1, ativa: false },
];

class DataFixa extends Date {
  constructor(...args) { if (args.length) super(...args); else super(2026, 10, 10, 12, 0, 0); }
}

test('proximaData: mesmo mês, mês seguinte, fim de mês e virada de ano', () => {
  const { contexto } = ambiente({ storage: storageFalso(), servidor: {} });
  const p = (dia, a, m, d) => contexto.proximaData(dia, new Date(a, m - 1, d));
  assert.equal(p(15, 2026, 11, 10), '2026-11-15');
  assert.equal(p(10, 2026, 11, 10), '2026-11-10');   // hoje conta
  assert.equal(p(5, 2026, 11, 10), '2026-12-05');
  assert.equal(p(31, 2026, 11, 10), '2026-11-30');   // novembro tem 30 dias
  assert.equal(p(5, 2026, 12, 31), '2027-01-05');
  assert.equal(p(30, 2027, 1, 31), '2027-02-28');
  assert.ok(contexto.diaValido(1) && contexto.diaValido(31));
  assert.ok(!contexto.diaValido(0) && !contexto.diaValido(32) && !contexto.diaValido(NaN) && !contexto.diaValido(2.5));
});

test('sincronizar processa vencidas antes de ler e atualiza as duas cópias locais', async () => {
  const storage = storageFalso({
    usuarioId: '5',
    poupe_gastos: '[{"valor":1}]',   // chave global antiga
    poupe_recorrencias_u5: JSON.stringify([
      { id: 'srv-1', origem: 'servidor', tipo: 'Gasto Fixo', valor: 999, dia: 1 },  // desatualizada
      { id: 77, tipo: 'Receita Fixa', valor: 3000, dia: 5, descricao: 'Salário' },   // local
    ]),
  });
  const servidor = {
    categorias: CATEGORIAS,
    recorrencias: REC_SERVIDOR,
    gastos: [{ id_gasto: 1, descricao: null, valor: '39.90', data: '2026-11-05', id_categoria: 1 }],
  };
  const { contexto, chamadas } = ambiente({ storage, servidor });
  assert.equal(await contexto.DadosLocais.sincronizar(), true);

  assert.deepEqual(chamadas[0], ['processar', '5']);   // gera gastos antes de listar
  const gastos = JSON.parse(storage.getItem('poupe_gastos_u5'));
  assert.deepEqual(gastos, [{ id: 1, descricao: '', valor: '39.90', data: '2026-11-05', categoria: 'Alimentação' }]);
  assert.equal(storage.getItem('poupe_gastos'), null);

  const rec = JSON.parse(storage.getItem('poupe_recorrencias_u5'));
  assert.equal(rec.length, 2);                          // ativa do servidor + receita local
  assert.equal(rec[0].id, 'srv-3');
  assert.equal(rec[0].tipo, 'Gasto Fixo');              // formato lido por caixa/score
  assert.equal(rec[0].dia, 5);
  assert.equal(rec[1].descricao, 'Salário');
  assert.ok(!rec.some(r => r.id === 'srv-1' || r.id === 'srv-4'));
});

test('falha no servidor mantém as cópias anteriores', async () => {
  const anteriores = { poupe_gastos_u5: '[{"valor":7}]', poupe_recorrencias_u5: '[{"id":1,"tipo":"Receita Fixa"}]' };
  const storage = storageFalso({ usuarioId: '5', ...anteriores });
  const servidor = { categorias: CATEGORIAS, falhas: ['processar', 'processarReceitas', 'listarRec', 'listarGastos', 'statusOrc', 'listarReceitas'] };
  const { contexto } = ambiente({ storage, servidor });
  assert.equal(await contexto.DadosLocais.sincronizar(), false);
  assert.equal(storage.getItem('poupe_gastos_u5'), anteriores.poupe_gastos_u5);
  assert.equal(storage.getItem('poupe_recorrencias_u5'), anteriores.poupe_recorrencias_u5);
});

test('gastos fixos antigos do navegador migram para o servidor; falhas ficam locais', async () => {
  const storage = storageFalso({
    usuarioId: '5',
    poupe_recorrencias_u5: JSON.stringify([
      { id: 1, tipo: 'Gasto Fixo', descricao: 'Aluguel', valor: 1200, dia: '5' },
      { id: 2, tipo: 'Gasto Fixo', descricao: 'Recusado', valor: 50, dia: '20' },
      { id: 3, tipo: 'Gasto Fixo', descricao: 'Dia inválido', valor: 10, dia: '' },
      { id: 4, tipo: 'Receita Fixa', descricao: 'Salário', valor: 3000, dia: '5' },
    ]),
  });
  const servidor = { categorias: CATEGORIAS, recusar: (d) => d.descricao === 'Recusado' };
  const { contexto, chamadas } = ambiente({ storage, servidor, Date: DataFixa });
  const migrados = await contexto.migrarGastosFixosLocais({ 1: 'alimentação', 10: 'outros' });

  assert.equal(migrados, 1);
  const criados = chamadas.filter(c => c[0] === 'criar').map(c => c[1]);
  assert.deepEqual(JSON.parse(JSON.stringify(criados[0])), {
    id_categoria: 10, valor: 1200, descricao: 'Aluguel', frequencia: 'mensal', proxima_data: '2026-12-05',
  });
  assert.equal(criados.length, 2);                      // o de dia inválido nem é enviado
  const restantes = JSON.parse(storage.getItem('poupe_recorrencias_u5')).map(r => r.id);
  assert.deepEqual(restantes, [2, 3, 4]);
});

test('migração não acontece sem a categoria "outros"', async () => {
  const storage = storageFalso({ usuarioId: '5', poupe_recorrencias_u5: '[{"id":1,"tipo":"Gasto Fixo","valor":5,"dia":"3"}]' });
  const { contexto, chamadas } = ambiente({ storage, servidor: {} });
  assert.equal(await contexto.migrarGastosFixosLocais({ 1: 'alimentação' }), 0);
  assert.equal(chamadas.length, 0);
});

test('telas que calculam no navegador sincronizam antes de ler', () => {
  for (const arquivo of ['score.html', 'cofrinho.html', 'desperdicio.html', 'caixa.html']) {
    const fonte = ler(arquivo);
    const inicio = fonte.indexOf('document.addEventListener("DOMContentLoaded", async () => {');
    const sincroniza = fonte.indexOf('await DadosLocais.sincronizar();', inicio);
    const leitura = fonte.indexOf('localStorage.getItem(chaveUsuario("poupe_', inicio);
    assert.ok(inicio >= 0 && sincroniza > inicio && sincroniza < leitura, arquivo);
  }
});

test('gastos.html processa recorrências antes de carregar os gastos', () => {
  const fonte = ler('gastos.html');
  const inicio = fonte.lastIndexOf('INICIAR PÁGINA');
  const processa = fonte.indexOf('await RecorrenciaAPI.processar(usuarioId);', inicio);
  const carrega = fonte.indexOf('await carregarGastos();', inicio);
  assert.ok(inicio >= 0 && processa > inicio && processa < carrega);
});

test('recorrencia.html não grava gastos fixos novos só no navegador', () => {
  const submit = trecho(recorrenciaHtml, 'formRecorrencia.addEventListener("submit"', 'atualizarCamposPorTipo();\n  renderizar();'.replace('\n', recorrenciaHtml.includes('\r\n') ? '\r\n' : '\n'));
  assert.ok(submit.includes('if (tipo === "Gasto Fixo")'));
  assert.ok(submit.includes('await RecorrenciaAPI.criar('));
  assert.ok(submit.includes('frequencia: "mensal"'));
});

// ---------------------------------------------------------------------------
// Item 10b: orçamentos no servidor
// ---------------------------------------------------------------------------

test('sincronizar grava orçamentos do servidor e preserva os que só existem localmente', async () => {
  const storage = storageFalso({
    usuarioId: '5',
    poupe_orcamentos_u5: JSON.stringify([
      { id: 'srv-9', origem: 'servidor', categoria: 'Velho', limite: 1 },   // desatualizado
      { id: 3, categoria: 'Inexistente', limite: 80 },                      // local pendente
    ]),
  });
  const servidor = {
    categorias: CATEGORIAS, recorrencias: [], gastos: [],
    orcamentos: [{ id_orcamento: 7, id_categoria: 1, categoria: 'alimentação', limite: 500,
                   gasto_mes: 420, restante: 80, percentual: 84, situacao: 'atencao' }],
  };
  const { contexto, chamadas } = ambiente({ storage, servidor });
  assert.equal(await contexto.DadosLocais.sincronizar(), true);
  assert.ok(chamadas.some(c => c[0] === 'statusOrc'));
  const lista = JSON.parse(storage.getItem('poupe_orcamentos_u5'));
  assert.deepEqual(lista.map(o => o.id), ['srv-7', 3]);
  assert.equal(lista[0].categoria, 'Alimentação');      // mesmo formato do cache de gastos
  assert.equal(lista[0].gasto_mes, 420);
  assert.equal(lista[0].situacao, 'atencao');
});

test('limites antigos migram pelo id da categoria; "Estudos" vira educação; sem par fica local', async () => {
  const storage = storageFalso({
    usuarioId: '5',
    poupe_orcamentos_u5: JSON.stringify([
      { id: 1, categoria: 'Alimentação', limite: 600 },
      { id: 2, categoria: 'Estudos', limite: 200 },
      { id: 3, categoria: 'Inexistente', limite: 80 },
      { id: 4, categoria: 'Lazer', limite: 0 },          // inválido
      { id: 5, categoria: 'Saúde', limite: 300 },        // servidor recusa
    ]),
  });
  const servidor = { recusar: (d) => d.id_categoria === 3 };
  const { contexto, chamadas } = ambiente({ storage, servidor });
  const ids = { 'alimentação': 1, 'educação': 6, 'lazer': 4, 'saúde': 3 };
  assert.equal(await contexto.migrarOrcamentosLocais(ids), 2);
  const enviados = chamadas.filter(c => c[0] === 'definirOrc').map(c => JSON.parse(JSON.stringify(c[1])));
  assert.deepEqual(enviados, [
    { id_categoria: 1, limite: 600 }, { id_categoria: 6, limite: 200 }, { id_categoria: 3, limite: 300 },
  ]);
  const restantes = JSON.parse(storage.getItem('poupe_orcamentos_u5')).map(o => o.id);
  assert.deepEqual(restantes, [3, 4, 5]);
});

test('orcamento.html usa o servidor: categorias por id, números do backend e verificação de alertas', () => {
  const fonte = ler('orcamento.html');
  assert.ok(!fonte.includes('<option value="Estudos">'));            // categorias vêm do banco
  assert.ok(fonte.includes('<select id="catOrcamento" required></select>'));
  assert.ok(fonte.includes('await OrcamentoAPI.definir({ id_categoria: idCategoria, limite })'));
  assert.ok(fonte.includes('Number(o.gasto_mes)'));
  assert.ok(!fonte.includes('localStorage.getItem(chaveUsuario("poupe_gastos"))'));
  assert.ok(fonte.includes('OrcamentoAPI.verificar(usuarioId)'));
  const fluxo = fonte.slice(fonte.lastIndexOf('await carregarCategorias();'));
  assert.ok(fluxo.indexOf('migrarOrcamentosLocais') < fluxo.indexOf('await atualizar();'));
});

test('score usa o gasto do mês vindo do servidor quando disponível', () => {
  const fonte = ler('score.html');
  assert.ok(fonte.includes('o.gasto_mes != null'));
});

// ---------------------------------------------------------------------------
// Item 10c: receitas no servidor
// ---------------------------------------------------------------------------

test('sincronizarReceitas grava no formato de score/relatórios, preserva locais e apaga a chave sem usuário', async () => {
  const storage = storageFalso({
    usuarioId: '5',
    poupePlus_incomes: '[{"amount":1,"description":"de outra conta"}]',
    poupePlus_incomes_u5: JSON.stringify([
      { id: 'srv-1', origem: 'servidor', description: 'Velha', amount: 1 },
      { description: 'Pendente', category: 'Outros', amount: 0, date: '2026-11-01' },
    ]),
  });
  const servidor = { receitas: [{ id_receita: 8, descricao: 'Salário', categoria: 'Salário', valor: 5000.5, data: '2026-11-05' }] };
  const { contexto } = ambiente({ storage, servidor });
  assert.equal(await contexto.DadosLocais.sincronizarReceitas('5'), true);
  const lista = JSON.parse(storage.getItem('poupePlus_incomes_u5'));
  assert.deepEqual(JSON.parse(JSON.stringify(lista[0])), {
    id: 'srv-8', id_receita: 8, origem: 'servidor', description: 'Salário', category: 'Salário', amount: 5000.5, date: '2026-11-05',
  });
  assert.equal(lista[1].description, 'Pendente');
  assert.equal(lista.length, 2);
  assert.equal(storage.getItem('poupePlus_incomes'), null);
});

test('receitas antigas migram; inválidas e recusadas ficam no navegador', async () => {
  const storage = storageFalso({
    usuarioId: '5',
    poupePlus_incomes_u5: JSON.stringify([
      { description: 'Salário', category: 'Salário', amount: 5000, date: '2026-10-05' },
      { description: 'Sem valor', category: 'Outros', amount: 0, date: '2026-10-06' },
      { description: 'Recusada', category: 'Herança', amount: 10, date: '2026-10-07' },
      { description: 'Freela', category: 'Trabalho', amount: '800.5', date: '2026-10-08' },
    ]),
  });
  const servidor = { recusar: (d) => d.categoria === 'Herança' };
  const { contexto, chamadas } = ambiente({ storage, servidor });
  assert.equal(await contexto.migrarReceitasLocais(), 2);
  const enviados = chamadas.filter(c => c[0] === 'criarReceita').map(c => JSON.parse(JSON.stringify(c[1])));
  assert.deepEqual(enviados, [
    { descricao: 'Salário', categoria: 'Salário', valor: 5000, data: '2026-10-05' },
    { descricao: 'Recusada', categoria: 'Herança', valor: 10, data: '2026-10-07' },
    { descricao: 'Freela', categoria: 'Trabalho', valor: 800.5, data: '2026-10-08' },
  ]);
  const restantes = JSON.parse(storage.getItem('poupePlus_incomes_u5')).map(r => r.description);
  assert.deepEqual(restantes, ['Sem valor', 'Recusada']);
});

test('hojeISO usa o dia local, não UTC', () => {
  const { contexto } = ambiente({ storage: storageFalso(), servidor: {} });
  assert.equal(contexto.hojeISO(new Date(2026, 10, 5, 23, 30)), '2026-11-05');
  assert.equal(contexto.hojeISO(new Date(2026, 0, 1, 0, 5)), '2026-01-01');
});

test('receitas.html: mês atual, servidor para salvar/excluir, sem chave global', () => {
  const fonte = ler('receitas.html');
  assert.ok(!fonte.includes('new Date(2026, 7, 1)'));
  assert.ok(!fonte.includes('.toISOString('));
  assert.ok(fonte.includes('await ReceitaAPI.criar({ descricao, categoria, valor, data })'));
  assert.ok(fonte.includes('await ReceitaAPI.excluir(item.id_receita)'));
  assert.ok(!/localStorage\.setItem\(\s*['"]poupePlus_incomes['"]/.test(fonte));
  const relatorios = ler('relatorios.html');
  assert.ok(relatorios.indexOf('await DadosLocais.sincronizarReceitas();') < relatorios.indexOf('await carregarDadosBase();'));
});

// ---------------------------------------------------------------------------
// Item 10c, parte 2: contas, metas, cofrinhos e receitas fixas
// ---------------------------------------------------------------------------

test('sincronizar processa gastos e receitas fixas e lista as duas no cache de recorrências', async () => {
  const storage = storageFalso({ usuarioId: '5' });
  const servidor = {
    categorias: CATEGORIAS, gastos: [], recorrencias: [],
    receitasFixas: [
      { id_receita_recorrente: 4, descricao: 'Salário', categoria: 'Salário', valor: 5000, dia_mes: 5, proxima_data: '2026-12-05', ativa: true },
      { id_receita_recorrente: 6, descricao: 'Pausada', categoria: 'Outros', valor: 1, dia_mes: 1, proxima_data: '2026-12-01', ativa: false },
    ],
  };
  const { contexto, chamadas } = ambiente({ storage, servidor });
  assert.equal(await contexto.DadosLocais.sincronizar(), true);
  assert.deepEqual(chamadas.slice(0, 2).map(c => c[0]).sort(), ['processar', 'processarReceitas']);
  const rec = JSON.parse(storage.getItem('poupe_recorrencias_u5'));
  assert.equal(rec.length, 1);
  assert.equal(rec[0].id, 'srvr-4');
  assert.equal(rec[0].tipo, 'Receita Fixa');        // formato que caixa/score leem
  assert.equal(rec[0].dia, 5);
});

test('formatos de cache mantêm os campos que as telas antigas leem', () => {
  const { contexto } = ambiente({ storage: storageFalso(), servidor: {} });
  const j = (x) => JSON.parse(JSON.stringify(x));
  assert.deepEqual(j(contexto.contaParaCache({ id_conta: 1, nome: 'Nu', tipo: 'Corrente', saldo: 10 })),
    { id: 'srv-1', id_conta: 1, origem: 'servidor', nome: 'Nu', tipo: 'Corrente', saldo: 10 });
  assert.deepEqual(j(contexto.cofrinhoParaCache({ id_cofrinho: 2, titulo: 'R', valor_alvo: 100, valor_guardado: 5, prazo_meses: 3 })),
    { id: 'srv-2', id_cofrinho: 2, origem: 'servidor', titulo: 'R', alvo: 100, guardado: 5, prazoMeses: 3 });
  assert.deepEqual(j(contexto.metaParaCache({ id_meta: 3, titulo: 'V', valor_alvo: 50, valor_guardado: 1 })),
    { id: 'srv-3', id_meta: 3, origem: 'servidor', title: 'V', target: 50, current: 1 });
});

test('migrarItensLocais: envia válidos, mantém inválidos/recusados e preserva itens do servidor', async () => {
  const storage = storageFalso({
    usuarioId: '5',
    poupe_contas_u5: JSON.stringify([
      { id: 'srv-1', origem: 'servidor', nome: 'Já no servidor', tipo: 'Corrente', saldo: 1 },
      { id: 10, nome: 'Nubank', tipo: 'Corrente', saldo: 100 },
      { id: 11, nome: 'Sem saldo', tipo: 'Corrente', saldo: 'abc' },
      { id: 12, nome: 'Recusada', tipo: 'Cripto', saldo: 5 },
    ]),
  });
  const servidor = { recusar: (d) => d.tipo === 'Cripto' };
  const { contexto, chamadas } = ambiente({ storage, servidor });
  const converter = (c) => (Number.isFinite(Number(c.saldo)) ? { nome: c.nome, tipo: c.tipo, saldo: Number(c.saldo) } : null);
  const n = await contexto.migrarItensLocais('poupe_contas', converter, contexto.ContaAPI.criar);
  assert.equal(n, 1);
  assert.deepEqual(chamadas.filter(c => c[0] === 'criarConta').map(c => c[1].nome), ['Nubank', 'Recusada']);
  const ids = JSON.parse(storage.getItem('poupe_contas_u5')).map(c => c.id);
  assert.deepEqual(ids, ['srv-1', 11, 12]);
});

test('sincronizarContas grava servidor + locais e mantém a cópia em falha', async () => {
  const storage = storageFalso({ usuarioId: '5', poupe_contas_u5: '[{"id":9,"nome":"Local","saldo":1}]' });
  const servidor = { contas: [{ id_conta: 1, nome: 'Nu', tipo: 'Corrente', saldo: 10 }] };
  const { contexto } = ambiente({ storage, servidor });
  assert.equal(await contexto.DadosLocais.sincronizarContas('5'), true);
  assert.deepEqual(JSON.parse(storage.getItem('poupe_contas_u5')).map(c => c.id), ['srv-1', 9]);
  servidor.falhas = ['listarContas'];
  const antes = storage.getItem('poupe_contas_u5');
  assert.equal(await contexto.DadosLocais.sincronizarContas('5'), false);
  assert.equal(storage.getItem('poupe_contas_u5'), antes);
});

test('metas.html: o script carrega sem api.js (que é "defer") e não grava em chave sem usuário', () => {
  const fonte = ler('metas.html');
  const script = fonte.slice(fonte.lastIndexOf('<script>') + 8, fonte.lastIndexOf('</script>'));
  const ouvintes = [];
  const contexto = vm.createContext({
    document: { getElementById: () => null, addEventListener: (ev, fn) => ouvintes.push(ev) },
    window: {},
  });
  vm.runInContext(script, contexto);     // antes: ReferenceError chaveUsuario is not defined
  assert.deepEqual(ouvintes, ['DOMContentLoaded']);
  assert.ok(!/localStorage\.setItem\(\s*['"]poupePlus_goals['"]/.test(fonte));
  assert.ok(!fonte.includes('onclick="deleteGoal('));
  assert.ok(fonte.includes('await MetaAPI.criar({ titulo, valor_alvo: alvo, valor_guardado: guardado })'));
});

test('caixa, cofrinho e recorrência gravam no servidor', () => {
  const caixa = ler('caixa.html');
  assert.ok(caixa.includes('await ContaAPI.criar({ nome, tipo, saldo })'));
  assert.ok(caixa.includes('await ContaAPI.excluir(conta.id_conta)'));
  assert.ok(!caixa.includes('contas.push('));
  const cofrinho = ler('cofrinho.html');
  assert.ok(cofrinho.includes('await CofrinhoAPI.aportar(item.id_cofrinho, num)'));
  assert.ok(cofrinho.includes('await CofrinhoAPI.criar({ titulo, valor_alvo: alvo, valor_guardado: guardado, prazo_meses: prazoMeses })'));
  assert.ok(!cofrinho.includes('metas.push('));
  const rec = ler('recorrencia.html');
  assert.ok(rec.includes('await ReceitaRecorrenteAPI.criar({'));
  assert.ok(rec.includes('await ReceitaRecorrenteAPI.excluir(item.id_receita_recorrente)'));
  assert.ok(!rec.includes('locais.push({ id: Date.now(), descricao, tipo, valor, dia })'));
});
