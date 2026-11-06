# Correções REV-001 a REV-003 — tentativas, sessões e scripts externos

Achados da revisão do Claude (seção 9 do CONTEXTO_DO_PROJETO.md).

## 1. Atualize o banco

Esta versão cria duas tabelas: `sessao_usuario` e `tentativa_acesso`.
Com um banco já instalado, o servidor não sobe até você rodar uma vez:

```powershell
python setup_db.py --atualizar
```

Só cria as tabelas que faltam; não apaga dados. Depois disso, todo mundo
precisa entrar de novo: cookies do formato antigo deixam de valer.

## 2. REV-001 — limite de tentativas

Antes, dava para testar milhares de senhas no `/login` sem nenhuma barreira.
Agora cada falha vira uma linha em `tentativa_acesso`:

| Regra | Padrão | Variável no `.env` |
|---|---|---|
| Falhas por e-mail na janela | 5 | `LOGIN_FALHAS_EMAIL` |
| Falhas por IP na janela | 30 | `LOGIN_FALHAS_IP` |
| Tamanho da janela (minutos) | 15 | `LOGIN_JANELA_MINUTOS` |
| Cadastros criados por IP por hora | 10 | `CADASTROS_IP_HORA` |

Passou do limite, a resposta é **429** com o cabeçalho `Retry-After`, mesmo
com a senha certa (senão a força bruta continuaria). O bloqueio é conferido
antes de calcular o hash, então também protege a CPU. Login certo zera o
contador daquele e-mail. Senha atual errada na troca de senha/e-mail conta
no mesmo contador. O e-mail é comparado sem diferenciar maiúsculas.

O IP é o da conexão (`request.remote_addr`). Atrás de um proxy reverso,
todos os usuários teriam o mesmo IP: nesse caso, configure o
`ProxyFix` do Werkzeug antes de publicar.

## 3. REV-002 — sessão que acaba de verdade

Antes, o cookie assinado valia por 8 h mesmo depois do logout, e bastava
para trocar a senha sem conhecer a atual. Agora:

1. O login gera um token aleatório; o cookie guarda o token e o banco guarda
   só o hash SHA-256 (`sessao_usuario`).
2. `backend/auth.py` confere se a sessão existe e não expirou.
3. **Logout** apaga a linha: um cookie copiado antes deixa de funcionar.
4. Trocar **senha** ou **e-mail** exige `senha_atual` (400 se faltar, 403 se
   errada) e desconecta os outros aparelhos; o atual continua logado.

Na tela `configuracoes.html`, "Segurança → Alterar senha" agora chama o
servidor (antes só mostrava a mensagem de sucesso) e o perfil pede a senha
atual quando o e-mail muda. Também foi corrigido um erro antigo da página:
ela redeclarava `themeButton` (já declarado em `api.js`), o que impedia todo
o script dela de rodar.

## 4. REV-003 — scripts só da própria origem

Antes, 15 páginas carregavam `https://unpkg.com/lucide@latest` e duas
`https://cdn.jsdelivr.net/npm/chart.js`, sem versão fixa nem verificação.
Um pacote alterado rodaria com a sessão do usuário. Agora:

- `frontend/vendor/lucide-1.69.0.min.js` (licença ISC) e
  `frontend/vendor/chart-4.6.1.umd.min.js` (licença MIT), com as licenças
  ao lado. Para atualizar: baixe a versão nova pelo npm, troque o arquivo e o
  nome nas páginas, e teste.
- Todas as respostas têm `Content-Security-Policy` (só `'self'`),
  `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` e
  `Referrer-Policy: same-origin`.
- `'unsafe-inline'` continua permitido porque as páginas ainda têm
  `<script>` e `onclick` embutidos. Próximo passo: movê-los para arquivos
  `.js` e remover `'unsafe-inline'`.

## 5. Testes

- `python -m unittest discover -s tests`: `tests/test_seguranca.py` tem 18
  testes; 16 falham no código anterior.
- `tests/e2e/e2e_seguranca.py` (banco descartável): bloqueio na tela de
  login, as 15 páginas com ícones e gráficos reais sem nenhuma requisição
  externa nem violação de CSP, troca de senha pela tela derrubando outro
  navegador, e cookie copiado → 401 após o logout.
- Para rodar todos os E2E seguidos, suba o servidor com
  `CADASTROS_IP_HORA=1000` (cada script cadastra um usuário).
