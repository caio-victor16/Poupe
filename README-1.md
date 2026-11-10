# 💰 Poupe+

O **Poupe+** é um aplicativo web de controle financeiro para **pequenos empreendedores** (donos de restaurantes e comércios), que ajuda a organizar gastos, boletos e orçamento e a **evitar o endividamento** com alertas e previsões automáticas, no lugar de papel e planilhas.

> **Turma:** _[preencher]_ · **Projeto:** Poupe+ · Veja a [equipe](#-equipe).

## 🎯 Problema e público-alvo

Pequenos negócios costumam controlar o dinheiro em cadernos ou planilhas, sem aviso quando os gastos passam do planejado e sem visão do fim do mês. O Poupe+ centraliza os gastos, os boletos a pagar, as receitas e o orçamento por categoria, e avisa o usuário **antes** de ele estourar o limite.

## 🛠️ Tecnologias

| Camada | Tecnologia |
|---|---|
| Backend / API | Python 3, Flask 3 |
| Banco de dados | MySQL, PyMySQL, Flask-SQLAlchemy (ORM) e Stored Procedures |
| Frontend | HTML5, CSS3 e JavaScript puro (Chart.js e Lucide em `frontend/vendor/`) |
| IA | Google Gemini (API REST, via `requests`) |
| Segurança | Hash de senha scrypt, sessões revogáveis, limite de tentativas, cabeçalhos de segurança (CSP) |

## 🏗️ Arquitetura

```
Interface (HTML/JS)  →  API Flask  →  Controller  →  Service  →  Model (ORM) / Repository (SQL)  →  MySQL
```

| Camada | Pasta | Responsabilidade |
|---|---|---|
| Controller | `backend/controllers/` | Recebe a requisição HTTP, chama o Service e devolve o JSON com o código HTTP. |
| Service | `backend/services/` | Regras de negócio e validações (ex.: pagar boleto, limite de gastos, contexto da IA). |
| Model | `backend/models/` | Entidades do domínio mapeadas com SQLAlchemy. As operações CRUD (`salvar`, `buscar_por_id`, `deletar`, `listar_por_usuario`) são feitas pelo ORM. |
| Repository | `backend/repositories/` | Consultas SQL: cada método chama uma **stored procedure** (`CALL sp_...`) e devolve o resultado. |
| Banco | `database/mysql/poupe.sql` | Tabelas e 14 stored procedures. |

> **Observação:** o CRUD simples usa o ORM direto nos Models. As consultas SQL (relatório, previsão, limite, orçamento, etc.) ficam nos Repositories. Alguns casos de uso (boletos, receitas e o contexto da IA) têm o Service acessando os Models, sem passar por um Repository.

**Frontend e API separados:** o frontend não acessa o banco. Todas as telas consomem a API por `fetch` (ver `requisicao()` em `frontend/api.js`), com módulos como `GastoAPI`, `BoletoAPI` e `RelatorioAPI`. Em desenvolvimento o Flask serve as telas e a API na mesma origem (`window.location.origin`); a comunicação continua sendo por requisições HTTP/JSON, visível na aba *Network* do navegador.

### Organização das pastas

```
Poupe/
├── backend/
│   ├── controllers/     # rotas HTTP (um Blueprint por recurso)
│   ├── services/        # regras de negócio, validações e IA
│   ├── models/          # entidades ORM (SQLAlchemy)
│   ├── repositories/    # consultas SQL (stored procedures)
│   ├── routes.py        # registro dos Blueprints
│   ├── auth.py          # política de acesso: rota negada até ser autorizada
│   ├── seguranca.py     # sessões revogáveis e limite de tentativas
│   ├── passwords.py     # hash de senha (scrypt)
│   ├── crud.py          # validadores e CRUD genérico (contas, metas, cofrinhos, receitas fixas)
│   ├── extensions.py    # instância do SQLAlchemy
│   ├── config.py        # configurações (variáveis de ambiente)
│   └── __init__.py      # Application Factory (create_app)
├── frontend/            # telas HTML/CSS/JS; api.js concentra as chamadas à API
│   └── vendor/          # Chart.js e Lucide servidos localmente (sem CDN)
├── database/mysql/      # poupe.sql (tabelas e procedures)
├── setup_db.py          # cria/atualiza o banco automaticamente
├── migrar_senhas.py     # converte senhas antigas para hash
├── run.py               # ponto de entrada
├── requirements.txt
├── .env.example         # modelo do .env
└── README.md
```

## ✅ 20 funcionalidades

O Poupe+ tem **20 funcionalidades**. As que vão além do CRUD (regra de negócio, cálculo ou automação) estão marcadas com ⭐.

| # | Funcionalidade | O que faz | Tela | Endpoints principais |
|---|---|---|---|---|
| F01 | Cadastro de usuário | Cria a conta com nome, e-mail, senha (guardada com hash), renda e limite de gastos | `cadastro.html` | `POST /usuarios` |
| F02 | Login e logout | Sessão no servidor, revogada ao sair, com limite de tentativas de login | `login.html` | `POST /login`, `POST /logout`, `GET /sessao` |
| F03 | Recuperar senha por e-mail | Link de redefinição válido por 30 min e de uso único (exige SMTP) | `esqueci-senha.html`, `redefinir-senha.html` | `POST /senha/esqueci`, `POST /senha/redefinir` |
| F04 | Perfil e configurações | Editar dados, renda e limite; trocar senha (exige a atual); tema claro/escuro | `configuracoes.html` | `GET/PUT /usuarios/<id>` |
| F05 ⭐ | **Painel inicial** | Saldo total da conta (todas as receitas − todos os gastos até hoje), resumo do mês, gráfico por categoria, evolução diária e últimos gastos | `inicio.html` | (usa as listas da API) |
| F06 | Gastos | Registrar, listar por mês e excluir gastos por categoria | `gastos.html` | `/gastos`, `GET /gastos/usuario/<id>`, `GET /categorias` |
| F07 ⭐ | **Alerta automático de limite** | Ao lançar um gasto, avisa quando o mês chega a 80% ou 100% do limite (um alerta de cada tipo por mês) | `gastos.html` → `alertas.html` | `GET /gastos/usuario/<id>/limite`, `POST /alertas/usuario/<id>/gerar-limite` |
| F08 | Central de alertas | Lista os alertas de limite, orçamento e boletos, com data e ícone por tipo | `alertas.html` | `GET /alertas/usuario/<id>` |
| F09 | Receitas | Registrar, editar e excluir entradas de dinheiro por categoria | `receitas.html` | `/receitas` |
| F10 ⭐ | **Receitas fixas** | Receita que se repete todo mês e é lançada sozinha na data certa | `receitas.html` | `/receitas-recorrentes`, `POST /receitas-recorrentes/usuario/<id>/processar` |
| F11 ⭐ | **Boletos: pagar e desfazer** | Pagar um boleto gera o gasto automaticamente (uma única vez, mesmo com cliques repetidos); o pagamento pode ser desfeito | `boletos.html` | `/boletos`, `POST /boletos/<id>/pagar`, `POST /boletos/<id>/desfazer-pagamento` |
| F12 ⭐ | **Boletos fixos e débito automático** | Boleto fixo cria o do mês seguinte; débito automático paga sozinho no vencimento; avisos de boleto a vencer e vencido | `boletos.html`, `alertas.html` | `POST /boletos/usuario/<id>/processar`, `GET /boletos/usuario/<id>/proximos` |
| F13 ⭐ | **Orçamento por categoria** | Limite mensal por categoria, quanto já foi usado e alerta ao se aproximar do limite | `orcamento.html` | `/orcamentos`, `GET /orcamentos/usuario/<id>`, `POST /orcamentos/usuario/<id>/verificar` |
| F14 ⭐ | **Relatório e previsão financeira** | Resumo e gráficos dos gastos e boletos e projeção do total do mês (média diária × dias do mês) | `relatorios.html` | `GET /relatorios/usuario/<id>`, `GET /previsoes/usuario/<id>` |
| F15 ⭐ | **Caixa** | Contas e carteiras com saldo e "radar": quanto dá para gastar por dia e por quantos dias o dinheiro dura | `caixa.html` | `/contas` |
| F16 | Metas financeiras | Metas de economia com valor alvo, valor guardado, prazo e progresso | `metas.html` | `/metas` |
| F17 ⭐ | **Cofrinho** | Reservas com aportes e simulação de quanto se juntaria arredondando o troco de cada gasto | `cofrinho.html` | `/cofrinhos`, `POST /cofrinhos/<id>/aportar` |
| F18 ⭐ | **Score financeiro** | Nota de 0 a 100 (excelente, moderada ou crítica) com diagnóstico a partir dos gastos × renda, dos orçamentos e dos boletos vencidos | `score.html` | (usa as listas da API) |
| F19 ⭐ | **Análise de desperdício** | Encontra categorias acima da média, assinaturas prováveis e gastos duplicados | `desperdicio.html` | (usa as listas da API) |
| F20 ⭐ | **Assistente de IA** | Conversa com a IA (Google Gemini), que recebe um resumo das finanças do próprio usuário e responde sobre elas | `ia.html` | `POST /ia` |

## 🗄️ Persistência e consultas

- **ORM:** os Models (`backend/models/`) usam Flask-SQLAlchemy e fazem o CRUD (ex.: `Gasto.salvar()`, `Alerta.buscar_por_id()`).
- **SQL no Repository:** cada consulta analítica é uma stored procedure chamada em `backend/repositories/`:

| Repository | Procedure |
|---|---|
| `gasto_repository` | `sp_gastos_categoria`, `sp_gastos_por_periodo`, `sp_verificar_limite_gastos` |
| `alerta_repository` | `sp_gerar_alerta_limite` |
| `boleto_repository` | `sp_boletos_proximos_vencimento` |
| `orcamento_repository` | `sp_orcamento_status_mes` |
| `relatorio_repository` | `sp_relatorio_financeiro` |
| `previsao_repository` | `sp_previsao_financeira` |
| `score_repository` | `sp_score_indicadores` |
| `caixa_repository` | `sp_caixa_calcular` |
| `cofrinho_repository` | `sp_cofrinho_simular` |
| `desperdicio_repository` | `sp_desperdicio_categorias_acima_media`, `sp_desperdicio_assinaturas_provaveis`, `sp_desperdicio_gastos_duplicados` |

## 🔐 Segurança

- Senhas guardadas com hash (scrypt); troca de senha ou e-mail exige a senha atual.
- Sessão no servidor, com cookie e revogada no logout; limite de tentativas de login e de cadastros por IP.
- Política de acesso em `backend/auth.py`: **rotas novas são negadas** até receberem autorização explícita, e cada usuário só acessa os próprios dados.
- Recuperação de senha por e-mail com token de uso único guardado apenas como hash.

## 🤖 Assistente de IA (Gemini)

- `POST /ia` envia a pergunta, as últimas mensagens da conversa e **um resumo agregado das finanças do usuário logado** (sem e-mail, telefone, senha ou ids internos).
- Os limites de uso da IA são do próprio Poupe+ e ficam em `instance/ia_limites.sqlite3`. Os padrões estão na tabela de variáveis abaixo.
- Se o modelo principal estiver sobrecarregado (503), inexistente (404) ou sem cota (429), o serviço tenta até 2 outros modelos *flash* que a chave possui, começando pelos que têm mais cota gratuita (`*-lite`). Um modelo sem cota fica 10 minutos fora das tentativas.
- Em caso de **timeout** a pergunta **não** é repetida em outro modelo, porque o Google pode já ter processado (e cobrado) a chamada.
- Sem `GEMINI_API_KEY`, o resto do sistema funciona normalmente e a IA responde que não está configurada.

### Problemas comuns da IA

| Mensagem na tela | Causa | O que fazer |
|---|---|---|
| "A chave GEMINI_API_KEY é inválida" | Chave errada ou com espaço/aspas | Gere outra em https://aistudio.google.com/apikey e cole sem aspas |
| "alta demanda no momento" (503) | Modelo sobrecarregado no Google | Aguarde; o app já tenta outros modelos |
| "limite de uso da IA foi atingido" (429) | Cota gratuita do Google esgotada (por modelo, por minuto e por dia) ou chave sem cota gratuita (`limit: 0` no terminal) | Use `GEMINI_MODEL=gemini-flash-lite-latest`; aguarde (a cota diária zera por volta das 5h de Brasília) ou crie a chave em um **projeto novo** no AI Studio |
| "demorou demais" | Modelo lento ou rede instável | Tente de novo; se repetir, troque `GEMINI_MODEL` para `gemini-flash-lite-latest` |
| "não está configurada… falta GEMINI_API_KEY" | O arquivo `.env` não existe (ex.: ficou com o nome `.env.example`) ou não tem a linha da chave | Confira o nome do arquivo e a linha `GEMINI_API_KEY=sua_chave` |

Para diagnosticar, olhe o terminal do servidor: ao iniciar, o `run.py` mostra `IA: ativada (modelo …)` ou `IA: DESATIVADA` (sem nunca exibir a chave), e cada falha do Google aparece como `Gemini HTTP <código> no modelo <nome>: <motivo>`. A cota é da chave da API e vale para todos os usuários do app.

## 🚀 Como executar

1. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows (PowerShell)
   source venv/bin/activate   # Linux/Mac
   ```
   > No PowerShell, se a execução de scripts estiver desabilitada: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
2. Instale as dependências:
   ```bash
   python -m pip install -r requirements.txt
   ```
3. Copie `.env.example` para `.env` (na raiz, junto do `run.py`) e preencha. O arquivo deve se chamar exatamente `.env`, com **uma variável por linha e sem aspas**.
4. Rode a aplicação. O banco é criado automaticamente na primeira execução:
   ```bash
   python run.py
   ```
5. Acesse o endereço que aparece no terminal (normalmente `http://127.0.0.1:5000`). **Não** abra os arquivos `.html` direto pela pasta: sem o servidor as telas não funcionam.

**Banco de dados**
- O instalador só cria o banco se ele não existir ou estiver vazio; nunca apaga nada sozinho.
- Ao atualizar o código com um banco já instalado: `python setup_db.py --atualizar` (cria só as tabelas novas e recria as procedures, sem apagar dados).
- Recriar do zero (**apaga os dados**): `python setup_db.py --reset --confirmar poupe`.
- Se tiver senhas antigas em texto puro: `python migrar_senhas.py` (uma vez).

**Erro "tentativa de acesso a um soquete" no Windows:** a porta 5000 está em uso ou reservada pelo sistema (Hyper-V, WSL, Docker). O `run.py` detecta isso e usa outra porta automaticamente (5001, 5050, 8000…); o endereço certo aparece no terminal. Para fixar uma porta, use `POUPE_PORT` no `.env`.

### Variáveis de ambiente

| Variável | Padrão | Para que serve |
|---|---|---|
| `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` | `localhost`, `3306`, `root`, vazio, `poupe` | Conexão com o MySQL |
| `SECRET_KEY` | aleatória a cada execução | Chave de sessão (defina um valor fixo em produção) |
| `GEMINI_API_KEY` | vazio | Chave da IA (opcional) |
| `GEMINI_MODEL` | `gemini-flash-latest` | Modelo principal |
| `GEMINI_MODEL_RESERVA` | descoberta automática | Modelos reserva, separados por vírgula |
| `IA_LIMITE_MINUTO` / `IA_LIMITE_DIA` | `5` / `50` | Mensagens de IA por usuário |
| `IA_LIMITE_GLOBAL_MINUTO` / `IA_LIMITE_GLOBAL_DIA` | `30` / `500` | Mensagens de IA de todos os usuários juntos |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USUARIO`, `SMTP_SENHA`, `SMTP_REMETENTE`, `SMTP_SSL` | vazio, `587`, … | E-mail de "esqueci a senha" (opcional) |
| `APP_URL` | endereço em que o servidor subiu | Endereço usado no link do e-mail |
| `POUPE_PORT` | `5000` | Porta preferida do servidor (se estiver ocupada, outra é escolhida) |
| `LOGIN_FALHAS_EMAIL`, `LOGIN_FALHAS_IP`, `LOGIN_JANELA_MINUTOS`, `CADASTROS_IP_HORA` | `5`, `30`, `15`, `10` | Limites de tentativas de login e cadastro |
| `POUPE_DEBUG` | `false` | Modo debug |
| `SESSION_COOKIE_SECURE` | `false` | Use `true` quando houver HTTPS |

> Nunca envie o `.env` para o GitHub nem o compartilhe: ele contém a senha do banco e a chave da IA. O `.env.example` **vai** para o GitHub, então deve ter só nomes de variáveis e valores de exemplo, nunca chaves reais.

## ⚠️ Limitações conhecidas

- **Score, desperdício, caixa e cofrinho** calculam no navegador a partir de dados sincronizados do servidor. O backend também tem rotas e procedures para isso (`/score`, `/desperdicios`, `/caixa`, `/cofrinho`), mas as telas não as chamam.
- **Login com Google** não está disponível.
- **Tabela `extrato`:** existe no banco, mas não tem model, rota nem tela.
- **IA:** depende da cota gratuita do Google, que pode esgotar ou ficar indisponível por alguns minutos.
- Não há termos de consentimento nem hospedagem pública do sistema nesta versão.
- `frontend/caixa (1).html` é uma cópia antiga da tela Caixa, sem link no menu, e pode ser removida.

## 👨‍💻 Equipe

- Arthur Teles Braga
- Caio Victor Soares Gonzaga
- João Gabriel Costa Galbas
- Maria Eduarda Cardoso
- Maria Eduarda da Silva
- Rafael Alves
- Arthur Spinola
