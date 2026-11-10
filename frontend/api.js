const API_URL = window.location.origin;

// Aberto pelo arquivo (file:///C:/.../cadastro.html) não há servidor: toda
// chamada falha com "Failed to fetch". Mostra como abrir do jeito certo.
if (window.location.protocol === 'file:') {
  document.addEventListener('DOMContentLoaded', () => {
    document.body.innerHTML = `
      <div style="max-width:520px;margin:12vh auto;padding:28px;font-family:system-ui,sans-serif;
                  background:#fff;color:#1f2937;border-radius:16px;box-shadow:0 8px 30px rgba(0,0,0,.12);line-height:1.5">
        <h2 style="margin:0 0 12px;color:#024731">Abra o Poupe+ pelo servidor</h2>
        <p style="margin:0 0 12px">Esta página foi aberta direto do arquivo, então ela não consegue falar com o backend.</p>
        <ol style="margin:0 0 12px;padding-left:20px">
          <li>No terminal, na pasta do projeto: <code>python run.py</code></li>
          <li>Abra o endereço que aparecer, por exemplo
            <a href="http://127.0.0.1:5000/" style="color:#024731;font-weight:600">http://127.0.0.1:5000</a></li>
        </ol>
      </div>`;
  });
}
// Somente para texto HTML e atributos entre aspas; não usar em JS, CSS ou URLs.
function textoHTML(valor) {
  const entidades = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
  return String(valor ?? '').replace(/[&<>"']/g, caractere => entidades[caractere]);
}
const themeButton = document.getElementById("toggle-theme");
const themeText = document.getElementById("theme-text");
const themeIcon = document.getElementById("theme-icon");

function chaveUsuario(nome) {
  return `${nome}_u${localStorage.getItem('usuarioId')}`;
}

function atualizarTema() {
  if (document.body.classList.contains("dark-mode")) {
    if (themeText) themeText.textContent = "Escuro";
    if (themeIcon) themeIcon.setAttribute("data-lucide", "moon");
  } else {
    if (themeText) themeText.textContent = "Claro";
    if (themeIcon) themeIcon.setAttribute("data-lucide", "sun");
  }
  if (window.lucide) {
    lucide.createIcons();
  }
}

// Verifica e aplica o tema salvo no localStorage
if (localStorage.getItem("poupe-theme") === "dark") {
  document.body.classList.add("dark-mode");
} else {
  document.body.classList.remove("dark-mode");
}

atualizarTema();

if (themeButton) {
  themeButton.addEventListener("click", function () {
    document.body.classList.toggle("dark-mode");

    if (document.body.classList.contains("dark-mode")) {
      localStorage.setItem("poupe-theme", "dark");
    } else {
      localStorage.setItem("poupe-theme", "light");
    }

    atualizarTema();
  });
}

// Função auxiliar genérica para chamadas HTTP
async function requisicao(endpoint, metodo = 'GET', dados = null) {
  const config = {
    method: metodo,
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', 'X-Poupe-Request': '1' }
  };
  if (dados) config.body = JSON.stringify(dados);

  let resposta;
  try {
    resposta = await fetch(`${API_URL}${endpoint}`, config);
  } catch (erroRede) {
    throw new Error('Não foi possível conectar ao servidor. Confira se o "python run.py" está rodando e se a página foi aberta pelo endereço dele.');
  }

  // Respostas sem corpo (ex.: DELETE -> 204) não são JSON válido;
  // tentar fazer JSON.parse('') quebrava todas as exclusões antes.
  const textoResposta = await resposta.text();
  let resultado = null;

  if (textoResposta) {
    try {
      resultado = JSON.parse(textoResposta);
    } catch (e) {
      throw new Error(`Rota ${endpoint} não retornou um JSON válido. Verifique o backend.`);
    }
  }

  if (!resposta.ok) {
    if (resposta.status === 401 && endpoint !== '/login') {
      localStorage.removeItem('usuarioId');
      window.location.href = 'login.html';
    }
    throw new Error((resultado && (resultado.mensagem || resultado.erro)) || 'Erro na requisição');
  }

  return resultado;
}

// 1. MÓDULO DE USUÁRIOS
const UsuarioAPI = {
  login: (email, senha) => requisicao('/login', 'POST', { email, senha }),
  cadastrar: (dados) => requisicao('/usuarios', 'POST', dados),
  obterPerfil: (usuarioId) => requisicao(`/usuarios/${usuarioId}`),
  atualizarPerfil: (usuarioId, dados) => requisicao(`/usuarios/${usuarioId}`, 'PUT', dados),
  alterarSenha: (usuarioId, senhaAtual, novaSenha) =>
    requisicao(`/usuarios/${usuarioId}`, 'PUT', { senha: novaSenha, senha_atual: senhaAtual })
};

// Recuperação de senha (telas esqueci-senha.html e redefinir-senha.html)
const SenhaAPI = {
  esqueci: (email) => requisicao('/senha/esqueci', 'POST', { email }),
  redefinir: (token, senha) => requisicao('/senha/redefinir', 'POST', { token, senha })
};

// 2. MÓDULO DE CATEGORIAS
const CategoriaAPI = {
  listar: () => requisicao('/categorias')
};

// 3. MÓDULO DE GASTOS
const GastoAPI = {
  listarPorUsuario: (usuarioId) => requisicao(`/gastos/usuario/${usuarioId}`),
  criar: (dadosGasto) => requisicao('/gastos', 'POST', dadosGasto),
  excluir: (gastoId) => requisicao(`/gastos/${gastoId}`, 'DELETE'),
  verificarLimite: (usuarioId) => requisicao(`/gastos/usuario/${usuarioId}/limite`)
};

// 4. MÓDULO DE ALERTAS
const AlertaAPI = {
  listarPorUsuario: (usuarioId) => requisicao(`/alertas/usuario/${usuarioId}`),
  marcarVisualizado: (alertaId) => requisicao(`/alertas/${alertaId}/visualizar`, 'PUT'),
  gerarAlertaLimite: (usuarioId) => requisicao(`/alertas/usuario/${usuarioId}/gerar-limite`, 'POST')
};

// 5. MÓDULO DE BOLETOS
const BoletoAPI = {
  listarPorUsuario: (usuarioId) => requisicao(`/boletos/usuario/${usuarioId}`),
  proximosVencimentos: (usuarioId) => requisicao(`/boletos/usuario/${usuarioId}/proximos`),
  criar: (dadosBoleto) => requisicao('/boletos', 'POST', dadosBoleto),
  atualizar: (id, dados) => requisicao(`/boletos/${id}`, 'PUT', dados),
  excluir: (id) => requisicao(`/boletos/${id}`, 'DELETE'),
  // Marca como pago e lança o gasto (opcional: { data_pagamento, valor }).
  pagar: (id, dados = {}) => requisicao(`/boletos/${id}/pagar`, 'POST', dados),
  desfazerPagamento: (id) => requisicao(`/boletos/${id}/desfazer-pagamento`, 'POST'),
  // Débitos automáticos vencidos + avisos de vencimento.
  processar: (usuarioId) => requisicao(`/boletos/usuario/${usuarioId}/processar`, 'POST')
};

// 5b. MÓDULO DE RECORRÊNCIAS DE GASTO (gastos fixos salvos no servidor)
const RecorrenciaAPI = {
  listarPorUsuario: (usuarioId) => requisicao(`/recorrencias/usuario/${usuarioId}`),
  criar: (dados) => requisicao('/recorrencias', 'POST', dados),
  excluir: (recorrenciaId) => requisicao(`/recorrencias/${recorrenciaId}`, 'DELETE'),
  // Gera os gastos das recorrências vencidas até hoje e avança a próxima data.
  processar: (usuarioId) => requisicao(`/recorrencias/usuario/${usuarioId}/processar`, 'POST')
};

// 5c. MÓDULO DE ORÇAMENTOS (limite mensal por categoria, no servidor)
const OrcamentoAPI = {
  // Retorna limite, gasto do mês atual, percentual e situação por categoria.
  statusDoMes: (usuarioId) => requisicao(`/orcamentos/usuario/${usuarioId}`),
  // Cria ou atualiza o limite da categoria (um por categoria).
  definir: (dados) => requisicao('/orcamentos', 'POST', dados),
  excluir: (orcamentoId) => requisicao(`/orcamentos/${orcamentoId}`, 'DELETE'),
  // Cria alertas de orçamento (no máximo um por categoria por dia).
  verificar: (usuarioId) => requisicao(`/orcamentos/usuario/${usuarioId}/verificar`, 'POST')
};

// 5d. MÓDULO DE RECEITAS (no servidor)
const ReceitaAPI = {
  listarPorUsuario: (usuarioId) => requisicao(`/receitas/usuario/${usuarioId}`),
  criar: (dados) => requisicao('/receitas', 'POST', dados),
  atualizar: (receitaId, dados) => requisicao(`/receitas/${receitaId}`, 'PUT', dados),
  excluir: (receitaId) => requisicao(`/receitas/${receitaId}`, 'DELETE')
};

// 5e. CONTAS DO CAIXA, METAS, COFRINHOS E RECEITAS FIXAS (no servidor)
function apiPorUsuario(prefixo) {
  return {
    listarPorUsuario: (usuarioId) => requisicao(`${prefixo}/usuario/${usuarioId}`),
    criar: (dados) => requisicao(prefixo, 'POST', dados),
    atualizar: (id, dados) => requisicao(`${prefixo}/${id}`, 'PUT', dados),
    excluir: (id) => requisicao(`${prefixo}/${id}`, 'DELETE'),
  };
}
const ContaAPI = apiPorUsuario('/contas');
const MetaAPI = apiPorUsuario('/metas');
const CofrinhoAPI = {
  ...apiPorUsuario('/cofrinhos'),
  // Soma no banco (sem ler-somar-gravar no navegador).
  aportar: (id, valor) => requisicao(`/cofrinhos/${id}/aportar`, 'POST', { valor }),
};
const ReceitaRecorrenteAPI = {
  ...apiPorUsuario('/receitas-recorrentes'),
  processar: (usuarioId) => requisicao(`/receitas-recorrentes/usuario/${usuarioId}/processar`, 'POST'),
};

// 6. MÓDULO DE RELATÓRIOS E PREVISÕES
const RelatorioAPI = {
  gerarResumo: (usuarioId) => requisicao(`/relatorios/usuario/${usuarioId}`),
  obterPrevisao: (usuarioId) => requisicao(`/previsoes/usuario/${usuarioId}`)
};

// 7. MÓDULO DE INTELIGÊNCIA ARTIFICIAL
const IAAPI = {

  // historico: [{ papel: 'usuario' | 'ia', texto }] das mensagens anteriores desta conversa.
  // O servidor junta um resumo das finanças do usuário logado (não precisa enviar).
  conversar: (mensagem, historico = []) => {
    return requisicao('/ia', 'POST', { mensagem, historico });
  }

};

// O ID local é apenas uma conveniência da interface. O servidor valida o cookie.
const Sessao = {
  obterUsuarioId: () => localStorage.getItem('usuarioId'),
  exigirLogin: () => {
    const id = localStorage.getItem('usuarioId');
    if (!id) {
      window.location.href = 'login.html';
      return null;
    }
    return id;
  },
  sair: async () => {
    await requisicao('/logout', 'POST');
    localStorage.removeItem('usuarioId');
    window.location.href = 'login.html';
  }
};

// ==========================================
// DADOS DO SERVIDOR GUARDADOS NO NAVEGADOR
// ==========================================
// Orçamento, score, cofrinho, desperdício e caixa calculam no navegador a
// partir de cópias locais (gastos, recorrências, orçamentos e receitas). DadosLocais.sincronizar() atualiza essas cópias com
// o servidor ao abrir cada tela. Em falha, mantém a cópia anterior.

function capitalizar(texto) {
  if (!texto) return texto;
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

// Formato único do gasto no cache local (usado também por gastos.html).
function gastoParaCache(g, nomeCategoriaPorId) {
  return {
    id: g.id_gasto,
    descricao: g.descricao || "",
    valor: g.valor,
    data: g.data,
    categoria: capitalizar(nomeCategoriaPorId[g.id_categoria] || "outros"),
  };
}

// Recorrência do servidor no formato que caixa.html e score.html já leem.
function recorrenciaParaCache(r) {
  return {
    id: `srv-${r.id_recorrencia}`,
    id_recorrencia: r.id_recorrencia,
    origem: "servidor",
    descricao: r.descricao || "",
    tipo: "Gasto Fixo",
    valor: r.valor,
    dia: r.dia_mes,
    frequencia: r.frequencia,
    proxima_data: r.proxima_data,
    id_categoria: r.id_categoria,
  };
}

// Orçamento do servidor; "categoria" no mesmo formato do cache de gastos.
function orcamentoParaCache(o) {
  return {
    id: `srv-${o.id_orcamento}`,
    id_orcamento: o.id_orcamento,
    origem: "servidor",
    id_categoria: o.id_categoria,
    categoria: capitalizar(o.categoria),
    limite: o.limite,
    gasto_mes: o.gasto_mes,
    percentual: o.percentual,
    situacao: o.situacao,
  };
}

// Receita do servidor no formato que score.html e relatorios.html já leem.
function receitaParaCache(r) {
  return {
    id: `srv-${r.id_receita}`,
    id_receita: r.id_receita,
    origem: "servidor",
    description: r.descricao,
    category: r.categoria,
    amount: r.valor,
    date: r.data,
  };
}

// Formatos antigos das telas, para o código de exibição continuar igual.
function receitaFixaParaCache(r) {
  return {
    id: `srvr-${r.id_receita_recorrente}`,
    id_receita_recorrente: r.id_receita_recorrente,
    origem: "servidor",
    descricao: r.descricao,
    tipo: "Receita Fixa",
    categoria: r.categoria,
    valor: r.valor,
    dia: r.dia_mes,
    proxima_data: r.proxima_data,
  };
}
function contaParaCache(c) {
  return { id: `srv-${c.id_conta}`, id_conta: c.id_conta, origem: "servidor",
           nome: c.nome, tipo: c.tipo, saldo: c.saldo };
}
function cofrinhoParaCache(c) {
  return { id: `srv-${c.id_cofrinho}`, id_cofrinho: c.id_cofrinho, origem: "servidor",
           titulo: c.titulo, alvo: c.valor_alvo, guardado: c.valor_guardado, prazoMeses: c.prazo_meses };
}
function metaParaCache(m) {
  return { id: `srv-${m.id_meta}`, id_meta: m.id_meta, origem: "servidor",
           title: m.titulo, target: m.valor_alvo, current: m.valor_guardado };
}

// Itens de uma cópia local que só existem neste navegador (não vieram do servidor).
function itensLocais(nome) {
  try {
    const lista = JSON.parse(localStorage.getItem(chaveUsuario(nome)) || "[]");
    return Array.isArray(lista) ? lista.filter(r => r && r.origem !== "servidor") : [];
  } catch (e) {
    return [];
  }
}

// Receitas fixas e gastos fixos antigos que ainda não foram para o servidor.
function recorrenciasLocais() {
  return itensLocais("poupe_recorrencias");
}

// Envia ao servidor os itens antigos que só existem no navegador. converter(item)
// devolve o corpo da requisição ou null (item inválido: continua local). Cada item
// só sai do navegador depois que o servidor confirmar. Retorna quantos migraram.
async function migrarItensLocais(nome, converter, criar) {
  const locais = itensLocais(nome);
  const migrados = new Set();
  for (const [indice, item] of locais.entries()) {
    const corpo = converter(item);
    if (!corpo) continue;
    try {
      await criar(corpo);
      migrados.add(indice);
    } catch (erro) {
      console.error(`Não foi possível migrar item de ${nome}:`, erro);
    }
  }
  if (migrados.size) {
    // Relê a cópia: mantém itens do servidor e os locais que não migraram.
    const atual = JSON.parse(localStorage.getItem(chaveUsuario(nome)) || "[]");
    const doServidor = Array.isArray(atual) ? atual.filter(i => i && i.origem === "servidor") : [];
    localStorage.setItem(chaveUsuario(nome),
      JSON.stringify([...doServidor, ...locais.filter((_, i) => !migrados.has(i))]));
  }
  return migrados.size;
}

// Regrava a cópia local `nome` com os itens do servidor + os que só existem aqui.
async function sincronizarCopia(nome, listar, paraCache) {
  try {
    const doServidor = await listar();
    localStorage.setItem(chaveUsuario(nome),
      JSON.stringify([...doServidor.map(paraCache), ...itensLocais(nome)]));
    return true;
  } catch (erro) {
    console.error(`Não foi possível atualizar ${nome}:`, erro);
    return false;
  }
}

const DadosLocais = {
  async sincronizar() {
    const usuarioId = Sessao.obterUsuarioId();
    if (!usuarioId) return false;
    // Lança débitos automáticos de boletos e receitas fixas vencidos antes de ler as
    // listas. (RecorrenciaAPI: só recorrências antigas não mensais; as mensais viraram boletos.)
    const processamentos = await Promise.allSettled([
      BoletoAPI.processar(usuarioId),
      RecorrenciaAPI.processar(usuarioId),
      ReceitaRecorrenteAPI.processar(usuarioId),
    ]);
    processamentos.filter(p => p.status === "rejected")
      .forEach(p => console.error("Não foi possível processar as recorrências:", p.reason));
    const resultados = await Promise.all([
      this.sincronizarGastos(usuarioId),
      this.sincronizarRecorrencias(usuarioId),
      this.sincronizarOrcamentos(usuarioId),
      this.sincronizarReceitas(usuarioId),
      this.sincronizarBoletos(usuarioId),
    ]);
    return resultados.every(Boolean);
  },

  // Cópia dos boletos (formato do servidor, com "situacao"), lida pelo Caixa e pelo Score.
  sincronizarBoletos(usuarioId = Sessao.obterUsuarioId()) {
    return sincronizarCopia("poupe_boletos", () => BoletoAPI.listarPorUsuario(usuarioId),
                            b => ({ ...b, origem: "servidor" }));
  },

  async sincronizarReceitas(usuarioId = Sessao.obterUsuarioId()) {
    try {
      const doServidor = await ReceitaAPI.listarPorUsuario(usuarioId);
      const lista = [...doServidor.map(receitaParaCache), ...itensLocais("poupePlus_incomes")];
      localStorage.setItem(chaveUsuario("poupePlus_incomes"), JSON.stringify(lista));
      // Chave antiga sem usuário (gravada pela exclusão antiga): vazava entre contas.
      localStorage.removeItem("poupePlus_incomes");
      return true;
    } catch (erro) {
      console.error("Não foi possível atualizar as receitas:", erro);
      return false;
    }
  },

  sincronizarContas(usuarioId = Sessao.obterUsuarioId()) {
    return sincronizarCopia("poupe_contas", () => ContaAPI.listarPorUsuario(usuarioId), contaParaCache);
  },

  sincronizarCofrinhos(usuarioId = Sessao.obterUsuarioId()) {
    return sincronizarCopia("poupe_cofrinhos", () => CofrinhoAPI.listarPorUsuario(usuarioId), cofrinhoParaCache);
  },

  sincronizarMetas(usuarioId = Sessao.obterUsuarioId()) {
    return sincronizarCopia("poupePlus_goals", () => MetaAPI.listarPorUsuario(usuarioId), metaParaCache);
  },

  async sincronizarOrcamentos(usuarioId = Sessao.obterUsuarioId()) {
    try {
      const doServidor = await OrcamentoAPI.statusDoMes(usuarioId);
      const lista = [...doServidor.map(orcamentoParaCache), ...itensLocais("poupe_orcamentos")];
      localStorage.setItem(chaveUsuario("poupe_orcamentos"), JSON.stringify(lista));
      return true;
    } catch (erro) {
      console.error("Não foi possível atualizar os orçamentos:", erro);
      return false;
    }
  },

  async sincronizarGastos(usuarioId = Sessao.obterUsuarioId()) {
    try {
      const [gastos, categorias] = await Promise.all([
        GastoAPI.listarPorUsuario(usuarioId),
        CategoriaAPI.listar(),
      ]);
      const nomes = {};
      categorias.forEach(c => { nomes[c.id_categoria] = c.nome; });
      localStorage.setItem(chaveUsuario("poupe_gastos"),
        JSON.stringify(gastos.map(g => gastoParaCache(g, nomes))));
      localStorage.removeItem("poupe_gastos");
      return true;
    } catch (erro) {
      console.error("Não foi possível atualizar os gastos:", erro);
      return false;
    }
  },

  async sincronizarRecorrencias(usuarioId = Sessao.obterUsuarioId()) {
    try {
      const [gastosFixos, receitasFixas] = await Promise.all([
        RecorrenciaAPI.listarPorUsuario(usuarioId),
        ReceitaRecorrenteAPI.listarPorUsuario(usuarioId),
      ]);
      const lista = [
        ...gastosFixos.filter(r => r.ativa).map(recorrenciaParaCache),
        ...receitasFixas.filter(r => r.ativa).map(receitaFixaParaCache),
        ...recorrenciasLocais(),
      ];
      localStorage.setItem(chaveUsuario("poupe_recorrencias"), JSON.stringify(lista));
      return true;
    } catch (erro) {
      console.error("Não foi possível atualizar as recorrências:", erro);
      return false;
    }
  },
};

// ==========================================
// INTEGRAÇÃO COM AS PÁGINAS DO FRONT-END
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
  if (!['/', '/login.html', '/cadastro.html', '/esqueci-senha.html', '/redefinir-senha.html'].includes(window.location.pathname)) {
    requisicao('/sessao').then(sessao => {
      if (localStorage.getItem('usuarioId') !== String(sessao.usuario_id)) {
        localStorage.setItem('usuarioId', sessao.usuario_id);
        window.location.reload();
      }
    }).catch(erro => console.error('Não foi possível validar a sessão:', erro));
  }
  document.querySelectorAll('a[href="login.html"]').forEach(link => {
    if (!link.querySelector('[data-lucide="log-out"], .lucide-log-out') && !link.classList.contains('logout-card')) return;
    link.addEventListener('click', async (event) => {
      event.preventDefault();
      try { await Sessao.sair(); } catch (erro) { alert(erro.message); }
    });
  });
  const caminhoAtual = window.location.pathname;

  // Lógica da tela de Cadastro (cadastro.html)
  if (caminhoAtual.includes('cadastro')) {
    const formCadastro = document.querySelector('form');
    const caixaTermos = document.getElementById('aceiteTermos');
    if (caixaTermos) {
      const avisoTermos = () => caixaTermos.setCustomValidity(
        caixaTermos.checked ? '' : 'Para continuar, marque que leu e aceita os termos.');
      avisoTermos();
      caixaTermos.addEventListener('change', avisoTermos);
    }

    if (formCadastro) {
      formCadastro.addEventListener('submit', async (e) => {
        e.preventDefault();

        const nome = document.getElementById('name')?.value.trim() || '';
        const email = document.getElementById('email')?.value.trim() || '';
        const senha = document.getElementById('password')?.value || '';
        const renda_mensal = parseFloat(document.getElementById('income')?.value || 0);
        const limite_gastos = parseFloat(document.getElementById('limit')?.value || 0);
        // LGPD: o aceite precisa ser marcado pela pessoa; o servidor recusa sem ele.
        const aceite_termos = document.getElementById('aceiteTermos')?.checked === true;
        if (!aceite_termos) {
          alert('Para criar a conta, leia e aceite os Termos de Uso e o Termo de Consentimento.');
          return;
        }

        const dadosUsuario = { nome, email, senha, renda_mensal, limite_gastos, aceite_termos };

        try {
          await UsuarioAPI.cadastrar(dadosUsuario);
          alert('Usuário cadastrado com sucesso!');
          window.location.href = 'login.html';
        } catch (erro) {
          alert(`Erro ao cadastrar: ${erro.message}`);
        }
      });
    }
  }

  // Lógica da tela de Login (login.html)
  if (caminhoAtual.includes('login') || caminhoAtual === '/') {
    const formLogin = document.querySelector('form');

    if (formLogin) {
      formLogin.addEventListener('submit', async (e) => {
        e.preventDefault();

        const email = document.getElementById('email')?.value.trim() || '';
        const senha = document.getElementById('password')?.value || '';

        try {
          const resposta = await UsuarioAPI.login(email, senha);

          if (resposta.usuario_id) {
            localStorage.setItem('usuarioId', resposta.usuario_id);
          }
          window.location.href = 'inicio.html';
        } catch (erro) {
          alert(`Erro ao fazer login: ${erro.message}`);
        }
      });
    }
  }
});
