const API_URL = 'http://127.0.0.1:5000';
const themeButton = document.getElementById("toggle-theme");
const themeText = document.getElementById("theme-text");
const themeIcon = document.getElementById("theme-icon");

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
    headers: { 'Content-Type': 'application/json' }
  };
  if (dados) config.body = JSON.stringify(dados);

  const resposta = await fetch(`${API_URL}${endpoint}`, config);

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
    throw new Error((resultado && (resultado.mensagem || resultado.erro)) || 'Erro na requisição');
  }

  return resultado;
}

// 1. MÓDULO DE USUÁRIOS
const UsuarioAPI = {
  login: (email, senha) => requisicao('/login', 'POST', { email, senha }),
  cadastrar: (dados) => requisicao('/usuarios', 'POST', dados),
  obterPerfil: (usuarioId) => requisicao(`/usuarios/${usuarioId}`),
  atualizarPerfil: (usuarioId, dados) => requisicao(`/usuarios/${usuarioId}`, 'PUT', dados)
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
  criar: (dadosBoleto) => requisicao('/boletos', 'POST', dadosBoleto)
};

// 6. MÓDULO DE RELATÓRIOS E PREVISÕES
const RelatorioAPI = {
  gerarResumo: (usuarioId) => requisicao(`/relatorios/usuario/${usuarioId}`),
  obterPrevisao: (usuarioId) => requisicao(`/previsoes/usuario/${usuarioId}`)
};

// Sessão simples baseada no id do usuário salvo no localStorage após o login.
// (Não é autenticação de verdade — apenas guarda a navegação entre telas.)
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
  sair: () => {
    localStorage.removeItem('usuarioId');
    window.location.href = 'login.html';
  }
};

// ==========================================
// INTEGRAÇÃO COM AS PÁGINAS DO FRONT-END
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
  const caminhoAtual = window.location.pathname;

  // Lógica da tela de Cadastro (cadastro.html)
  if (caminhoAtual.includes('cadastro')) {
    const formCadastro = document.querySelector('form');

    if (formCadastro) {
      formCadastro.addEventListener('submit', async (e) => {
        e.preventDefault();

        const nome = document.getElementById('name')?.value.trim() || '';
        const email = document.getElementById('email')?.value.trim() || '';
        const senha = document.getElementById('password')?.value || '';
        const renda_mensal = parseFloat(document.getElementById('income')?.value || 0);
        const limite_gastos = parseFloat(document.getElementById('limit')?.value || 0);

        const dadosUsuario = { nome, email, senha, renda_mensal, limite_gastos };

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
