# 💰 Poupe+

O **Poupe+** é um aplicativo de controle financeiro desenvolvido para auxiliar pequenos empreendedores, especialmente proprietários de restaurantes e comércios, na organização de suas finanças e na prevenção de endividamento.

O sistema automatiza o gerenciamento financeiro por meio do registro de gastos, boletos e categorias, além de análises e previsões sobre os dados cadastrados, reduzindo a necessidade de controles manuais em papéis ou planilhas.

## 🎯 Objetivo

Oferecer uma ferramenta simples e inteligente para ajudar usuários a controlarem seus gastos, planejarem melhor suas finanças e tomarem decisões financeiras mais seguras.

## 🛠️ Tecnologias

- Python / Flask
- MySQL (PyMySQL + Flask-SQLAlchemy)
- HTML5, CSS3 e JavaScript
- Flask-CORS

## 🏗️ Arquitetura

O projeto segue a arquitetura em camadas trabalhada em aula:

```
Interface/Tela → API Flask → Controller → Service → Model/Repository → Banco de Dados
```

### Organização das pastas

```
Poupe/
├── backend/
│   ├── controllers/     # Recebem a requisição HTTP, chamam o Service e devolvem a resposta da API
│   ├── services/        # Regras de negócio e validações
│   ├── models/          # Entidades do domínio (ORM / SQLAlchemy)
│   ├── repositories/    # Acesso e persistência de dados
│   ├── routes.py        # Registro centralizado de todos os Blueprints (rotas) da API
│   ├── extensions.py    # Instâncias compartilhadas do Flask (SQLAlchemy, CORS)
│   ├── config.py        # Configurações da aplicação (variáveis de ambiente, banco de dados)
│   └── __init__.py      # Application Factory (create_app)
├── frontend/             # Telas (HTML/CSS/JS) que consomem a API
├── database/
│   └── mysql/            # Script de criação do banco, tabelas e Stored Procedures (poupe.sql)
├── docs/                 # Material de apoio (ex.: versão do login com Firebase, guardada para referência)
├── setup_db.py           # Cria o banco automaticamente a partir de poupe.sql
├── run.py                # Ponto de entrada da aplicação
├── requirements.txt
├── .env.example          # Modelo do arquivo .env (copie para .env e preencha)
└── README.md
```

> Cada funcionalidade completa passa obrigatoriamente por todas as camadas: **Interface → API Flask → Controller → Service → Model/Repository → Banco de Dados.**

## ✅ Funcionalidades ativas (front-end conectado ao backend)

Estas 10 funcionalidades já funcionam de ponta a ponta — a tela chama a API Flask, que passa por Controller → Service → Model/Repository → MySQL:

1. **Cadastrar usuário** (`cadastro.html` → `POST /usuarios`)
2. **Login do usuário** (`login.html` → `POST /login`)
3. **Consultar e editar perfil** (`configuracoes.html` → `GET/PUT /usuarios/<id>`)
4. **Listar categorias** (usado no formulário de gastos → `GET /categorias`)
5. **Cadastrar gasto** (`gastos.html` → `POST /gastos`)
6. **Listar gastos do usuário** (`gastos.html` → `GET /gastos/usuario/<id>`)
7. **Excluir gasto** (`gastos.html` → `DELETE /gastos/<id>`)
8. **Verificar limite de gastos + gerar alerta automático** (`gastos.html`, ao cadastrar um gasto → `GET /gastos/usuario/<id>/limite` e `POST /alertas/usuario/<id>/gerar-limite`)
9. **Listar alertas do usuário** (`alertas.html` → `GET /alertas/usuario/<id>`)
10. **Relatório financeiro + previsão financeira** (`relatorios.html` → `GET /relatorios/usuario/<id>` e `GET /previsoes/usuario/<id>`)
O backend também expõe rotas de atualização, boletos, orçamento, recorrência, caixa, cofrinho, desperdício, score e IA (ver seção "Funcionalidades da API" abaixo), mas as 10 acima são as que têm tela conectada de verdade nesta versão.

### ⚠️ Limitações conhecidas

- **Autenticação**: login com sessão no servidor (cookie HttpOnly, revogada no logout), limite de tentativas e troca de senha/e-mail exigindo a senha atual. Ver [docs/autenticacao-passo-a-passo.md](docs/autenticacao-passo-a-passo.md) e [docs/seguranca-acesso-passo-a-passo.md](docs/seguranca-acesso-passo-a-passo.md).
- **Senhas**: guardadas com hash (scrypt); ver [docs/senhas-passo-a-passo.md](docs/senhas-passo-a-passo.md).
- **Login com Google e "Esqueci a senha"** não estão disponíveis: exigiam o Firebase, que estava com chaves de exemplo e gravava o `uid` do Firebase como `usuarioId` (texto), enquanto toda a API usa o `id_usuario` numérico do MySQL. A versão com Firebase está guardada em `docs/login-firebase.html`.
- **Telas ainda sem integração com a API** (usam apenas `localStorage`, então os dados não são compartilhados entre dispositivos e se perdem ao limpar o cache): `receitas.html`, `metas.html`, `caixa.html`, `cofrinho.html`, `orcamento.html`, `recorrencia.html`, `desperdicio.html` e `score.html`. O backend dessas funcionalidades (exceto receitas e metas) já existe — falta ligar as telas a ele.
- **`ia.html`**: a rota `POST /ia` (Gemini) existe no backend e responde, mas a tela ainda é estática e não chama a rota. Requer `GEMINI_API_KEY` no `.env`; sem ela o restante do sistema funciona normalmente e a rota devolve uma mensagem de "IA não configurada".
- **`inicio.html`** (painel inicial) ainda exibe dados fixos de exemplo, sem chamar a API.
- **Tabela `extrato`**: existe no banco (`poupe.sql`) mas não tem model/rota — reservada para uma funcionalidade futura.

## 📋 Funcionalidades da API (backend completo)

1. Cadastrar, listar, consultar, atualizar e excluir usuário
2. Login do usuário
3. Cadastrar, listar (geral e por usuário), consultar, atualizar e excluir gasto
4. Listar gastos por categoria e por período
5. Verificar limite de gastos do usuário
6. Cadastrar, listar, atualizar e excluir categorias
7. Cadastrar, listar (geral e por usuário), atualizar e excluir boletos, e consultar boletos próximos do vencimento
8. Cadastrar, listar e excluir alertas do usuário, incluindo geração automática de alerta de limite
9. Gerar relatório financeiro do usuário
10. Gerar previsão financeira do usuário
11. Orçamento por categoria (limite mensal e status do mês)
12. Gastos recorrentes
13. Caixa (projeção), cofrinho (simulação de arredondamento), desperdício e score financeiro
14. Conversar com a IA (Gemini) sobre finanças

## 🚀 Como executar

1. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows (PowerShell)
   source venv/bin/activate   # Linux/Mac
   ```
   > No PowerShell, se aparecer "a execução de scripts foi desabilitada", rode antes:
   > `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
2. Instale as dependências:
   ```bash
   python -m pip install -r requirements.txt
   ```
3. Copie `.env.example` para `.env` (na raiz do projeto, junto do `run.py`) e preencha com a senha do seu MySQL. **Cada variável em uma linha própria**; o arquivo precisa se chamar exatamente `.env`:
   ```
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=sua_senha
   MYSQL_DATABASE=poupe
   GEMINI_API_KEY=            # opcional (só para a IA)
   SMTP_HOST=smtp.gmail.com   # opcional: e-mail de "esqueci a senha"
   SMTP_USUARIO=seuemail@gmail.com
   SMTP_SENHA=senha_de_app_do_gmail
   ```
4. Rode a aplicação — o banco é criado automaticamente na primeira execução (via `setup_db.py`):
   ```bash
   python run.py
   ```
   > O instalador só cria o banco se ele não existir ou estiver vazio; nunca apaga nada sozinho. Se o banco de `MYSQL_DATABASE` estiver incompleto (ex.: versão antiga sem `orcamento_categoria`/`recorrencia_gasto`) ou tiver tabelas de outro sistema, o servidor não sobe e explica o motivo. Para recriar tudo do zero (**apaga os dados**, faça backup antes): `python setup_db.py --reset --confirmar poupe`. Detalhes em [docs/banco-passo-a-passo.md](docs/banco-passo-a-passo.md).
   > Ao atualizar o código com um banco já instalado (o servidor avisa "versão anterior do Poupe+"), rode uma vez `python setup_db.py --atualizar`: cria só as tabelas novas e recria as procedures, sem apagar dados. A versão com as correções REV-001 a REV-003 (limite de tentativas, sessões revogáveis, scripts locais) cria `sessao_usuario` e `tentativa_acesso` e exige esse comando; veja [docs/seguranca-acesso-passo-a-passo.md](docs/seguranca-acesso-passo-a-passo.md).
5. Acesse `http://127.0.0.1:5000` no navegador — o backend também serve as telas de `frontend/`.

O modo debug fica desativado por padrão (`POUPE_DEBUG=false`). Veja o
[guia de erros e debug](docs/erros-debug-passo-a-passo.md) para entender as
mensagens de erro, os códigos de referência e a configuração de desenvolvimento.

## 👨‍💻 Equipe

- Arthur Teles Braga;
- Caio Victor Soares Gonzaga;
- João Gabriel Costa Galbas;
- Maria Eduarda Cardoso;
- Maria Eduarda da Silva;
- Rafael Alves;
- Arthur Spinola.
