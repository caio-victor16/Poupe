document.addEventListener('DOMContentLoaded', () => {
  const messages = document.getElementById('messages');
  const input = document.getElementById('messageInput');
  const button = document.getElementById('sendButton');
  const welcome = document.getElementById('welcome');
  const counter = document.getElementById('characterCount');
  let enviando = false;
  // Conversa desta aba (some ao recarregar). Vai junto para a IA lembrar o contexto.
  const historico = [];
  const MAX_HISTORICO = 10;

  function atualizarInput() {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 144) + 'px';
    counter.textContent = `${input.value.length} / 2000`;
    button.disabled = enviando || !input.value.trim();
  }

  document.querySelectorAll('[data-prompt]').forEach(suggestion => {
    suggestion.addEventListener('click', () => {
      input.value = suggestion.dataset.prompt;
      atualizarInput();
      input.focus();
    });
  });

  function adicionarMensagem(texto, tipo, extraClasse = '') {
    const msg = document.createElement('div');
    msg.className = 'message ' + tipo;
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.setAttribute('aria-hidden', 'true');
    const icon = document.createElement('i');
    icon.setAttribute('data-lucide', tipo === 'user-message' ? 'user' : 'sparkles');
    avatar.appendChild(icon);
    const box = document.createElement('div');
    box.className = 'message-box ' + extraClasse;
    // Nunca interpretar a mensagem do usuário ou a resposta da IA como HTML.
    box.textContent = texto;
    msg.append(avatar, box);
    messages.appendChild(msg);
    if (window.lucide) lucide.createIcons();
    messages.scrollTop = messages.scrollHeight;
    return msg;
  }

  async function enviar(event) {
    if (event) event.preventDefault();
    const texto = input.value.trim();
    if (!texto || enviando || texto.length > 2000) return;
    enviando = true;
    input.value = '';
    welcome.hidden = true;
    atualizarInput();
    adicionarMensagem(texto, 'user-message');
    const carregando = adicionarMensagem('Pensando na sua pergunta…', 'ai-message', 'typing');
    try {
      const resultado = await IAAPI.conversar(texto, historico.slice(-MAX_HISTORICO));
      carregando.remove();
      adicionarMensagem(resultado.resposta, 'ai-message');
      historico.push({ papel: 'usuario', texto }, { papel: 'ia', texto: resultado.resposta });
    } catch (erro) {
      carregando.remove();
      adicionarMensagem(erro instanceof TypeError
        ? 'Não foi possível conectar. Confira sua conexão e tente novamente.'
        : erro.message, 'ai-message error-message');
      // Recupera a pergunta sem sobrescrever um próximo rascunho já digitado.
      if (!input.value) input.value = texto;
    } finally {
      enviando = false;
      atualizarInput();
      input.focus();
    }
  }
  document.getElementById('chatForm').addEventListener('submit', enviar);
  input.addEventListener('input', atualizarInput);
  input.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) enviar(event);
  });
  atualizarInput();
  if (window.lucide) lucide.createIcons();
});
