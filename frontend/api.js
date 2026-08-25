const API_URL = 'http://127.0.0.1:5000';

// Função auxiliar genérica para chamadas HTTP
async function requisicao(endpoint, metodo = 'GET', dados = null) {
  const config = {
    method: metodo,
    headers: { 'Content-Type': 'application/json' }
  };
  if (dados) config.body = JSON.stringify(dados);

  try {
    const resposta = await fetch(`${API_URL}${endpoint}`, config);
    const textoResposta = await resposta.text();

    let resultado;
    try {
      resultado = JSON.parse(textoResposta);
    } catch (e) {
      throw new Error(`Rota ${endpoint} não retornou um JSON válido. Verifique o backend.`);
    }

    if (!resposta.ok) throw new Error(resultado.mensagem || resultado.erro || 'Erro na requisição');
    return resultado;
  } catch (erro) {
    console.error(`Erro ao acessar ${endpoint}:`, erro);
    throw erro;
  }
}

// 1. MÓDULO DE USUÁRIOS
const UsuarioAPI = {
  // Testa primeiro /login, caso a rota no seu controlador esteja sem o prefixo /usuarios
  login: (email, senha) => requisicao('/login', 'POST', { email, senha }),
  cadastrar: (dados) => requisicao('/usuarios', 'POST', dados),
  obterPerfil: (usuarioId) => requisicao(`/usuarios/${usuarioId}`),
  atualizarPerfil: (usuarioId, dados) => requisicao(`/usuarios/${usuarioId}`, 'PUT', dados)
};

// 2. MÓDULO DE GASTOS E RECEITAS
const GastoAPI = {
  listar: (usuarioId) => requisicao(`/gastos?usuario_id=${usuarioId}`),
  criar: (dadosGasto) => requisicao('/gastos', 'POST', dadosGasto),
  excluir: (gastoId) => requisicao(`/gastos/${gastoId}`, 'DELETE')
};

// 3. MÓDULO DE CATEGORIAS
const CategoriaAPI = {
  listar: () => requisicao('/categorias')
};

// 4. MÓDULO DE ALERTAS
const AlertaAPI = {
  listar: (usuarioId) => requisicao(`/alertas?usuario_id=${usuarioId}`),
  criar: (dadosAlerta) => requisicao('/alertas', 'POST', dadosAlerta)
};

// 5. MÓDULO DE BOLETOS
const BoletoAPI = {
  listar: (usuarioId) => requisicao(`/boletos?usuario_id=${usuarioId}`),
  criar: (dadosBoleto) => requisicao('/boletos', 'POST', dadosBoleto)
};

// 6. MÓDULO DE RELATÓRIOS E PREVISÕES
const RelatorioAPI = {
  gerarResumo: (usuarioId) => requisicao(`/relatorios?usuario_id=${usuarioId}`),
  obterPrevisao: (usuarioId) => requisicao(`/previsao?usuario_id=${usuarioId}`)
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
          const resposta = await UsuarioAPI.cadastrar(dadosUsuario);
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
          // Tentativa principal de login
          let resposta;
          try {
            resposta = await UsuarioAPI.login(email, senha);
          } catch (err) {
            // Tenta rota alternativa se o controller usar /usuarios/login
            resposta = await requisicao('/usuarios/login', 'POST', { email, senha });
          }

          alert('Login efetuado com sucesso!');
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