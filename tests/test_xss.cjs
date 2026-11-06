// Executar: node --test tests/test_xss.cjs
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.join(__dirname, '..', 'frontend');
const api = fs.readFileSync(path.join(root, 'api.js'), 'utf8');
const helper = api.slice(api.indexOf('function textoHTML'), api.indexOf('const themeButton'));
const context = vm.createContext({});
vm.runInContext(helper, context);

test('escapa tags, atributos e entidades sem perder textos normais', () => {
  assert.equal(context.textoHTML(`<img src=x onerror="alert('x')">&`),
    '&lt;img src=x onerror=&quot;alert(&#39;x&#39;)&quot;&gt;&amp;');
  assert.equal(context.textoHTML('João — café R$ 10'), 'João — café R$ 10');
  assert.equal(context.textoHTML(null), '');
  assert.equal(context.textoHTML('&lt;script&gt;'), '&amp;lt;script&amp;gt;');
});

const cases = {
  'alertas.html': ['alert.title', 'alert.description', 'alert.date'],
  'caixa.html': ['c.nome', 'c.tipo', 'c.id'],
  'caixa (1).html': ['c.nome', 'c.tipo', 'c.id'],
  'cofrinho.html': ['m.titulo', 'm.id', 'meses'],
  'desperdicio.html': ['g.descricao', 'g.categoria'],
  'recorrencia.html': ['r.descricao', 'r.dia', 'r.id'],   // tipo: ver teste próprio abaixo
  'metas.html': ['goal.title'],
  'orcamento.html': ['o.categoria', 'o.id'],
  'receitas.html': ['item.description', 'item.category'],
  'gastos.html': ['gasto.categoria', 'gasto.id'],
};
for (const [file, fields] of Object.entries(cases)) {
  test(`${file}: campos externos escapados nos templates reais`, () => {
    const source = fs.readFileSync(path.join(root, file), 'utf8');
    const payload = `"><img src=x onerror='alert(1)'><svg onload=alert(2)>`;
    const variables = { textoHTML: context.textoHTML };
    for (const field of fields) {
      const [obj, prop] = field.split('.');
      if (prop) (variables[obj] ??= {})[prop] = payload;
      else variables[obj] = payload;
      const interpolation = '${textoHTML(' + field + ')}';
      assert.ok(source.includes(interpolation), field);
      assert.ok(!source.includes('${' + field + '}'), field);
      // Usa a expressão real da página tanto em texto quanto em atributo citado.
      const result = vm.runInNewContext('`<p>' + interpolation + '</p><button data-id="' + interpolation + '"></button>`', variables);
      assert.ok(!result.includes(payload));
      assert.ok(!result.includes('<img'));
      assert.ok(!result.includes('<svg'));
      assert.ok(result.includes('&quot;&gt;&lt;img'));
    }
  });
}

test('recorrencia.html: tipo e próxima data passam por textoHTML', () => {
  const source = fs.readFileSync(path.join(root, 'recorrencia.html'), 'utf8');
  assert.ok(source.includes('${textoHTML(descreverTipo(r))}'));
  assert.ok(source.includes('${textoHTML(proxima)}'));
  assert.ok(source.includes('${textoHTML(avisoSincronizacao)}'));
  // ${r.tipo} só aparece dentro de descreverTipo (texto puro, escapado no uso).
  const funcao = source.slice(source.indexOf('function descreverTipo'), source.indexOf('function renderizar'));
  assert.equal(source.split('${r.tipo}').length - 1, 1);
  assert.ok(funcao.includes('${r.tipo}'));
  assert.ok(!source.includes('${descreverTipo(r)}'));
});

test('scripts de todas as páginas continuam sintaticamente válidos', () => {
  new vm.Script(api);
  for (const file of fs.readdirSync(root).filter(f => f.endsWith('.html'))) {
    const source = fs.readFileSync(path.join(root, file), 'utf8');
    for (const match of source.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/gi)) {
      new vm.Script(match[1], { filename: file });
    }
  }
});
