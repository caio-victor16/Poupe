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
│   └── mysql/            # Scripts de criação do banco (bd.sql) e Stored Procedures (procedures.sql)
├── run.py                 # Ponto de entrada da aplicação
├── requirements.txt
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

O backend também expõe rotas de atualização, boletos e mais consultas (ver seção "Funcionalidades da API" abaixo), mas as 10 acima são as que têm tela conectada de verdade nesta versão.

### ⚠️ Limitações conhecidas

- **Sem autenticação real**: o login apenas confere e-mail/senha e guarda o `id` do usuário no `localStorage` do navegador. Não há token/sessão — qualquer pessoa com o `id` de outro usuário pode, hoje, chamar a API diretamente e acessar os dados dele. Não usar em produção sem implementar autenticação (ex.: JWT) antes.
- **Senha em texto puro**: por decisão do time nesta fase do projeto, as senhas não são criptografadas (hash) no banco.
- **Receitas, Metas e o Assistente de IA** (`receitas.html`, `metas.html`, `ia.html`) ainda não têm tabela/rota correspondente no backend. `receitas.html` e `metas.html` funcionam apenas com `localStorage` (os dados não são compartilhados entre dispositivos e são perdidos se o cache do navegador for limpo); `ia.html` é uma tela estática, sem lógica de envio de mensagens.
- **`inicio.html`** (painel inicial) ainda exibe dados fixos de exemplo, sem chamar a API.
- **Tabela `extrato`**: existe no banco (`bd.sql`) mas não tem model/rota — reservada para uma funcionalidade futura.

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

## 🚀 Como executar

1. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   source venv/bin/activate   # Linux/Mac
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Crie um arquivo `.env` na raiz do projeto com as credenciais do banco:
   ```
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=
   MYSQL_DATABASE=poupe
   ```
4. Execute o script `database/mysql/bd.sql` no MySQL para criar o banco e as tabelas, e em seguida `database/mysql/procedures.sql` para criar as Stored Procedures.
5. Rode a aplicação:
   ```bash
   python run.py
   ```
6. Acesse `http://127.0.0.1:5000` no navegador — o backend também serve as telas de `frontend/`.

## 👨‍💻 Equipe

- Arthur Teles Braga
- Caio Victor Soares Gonzaga
- João Gabriel Costa Galbas
- Maria Eduarda Cardoso
- Maria Eduarda da Silva
- Rafael Alves
- Arthur Spinola
