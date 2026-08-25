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

## ✅ Funcionalidades Implementadas

1. Cadastrar usuário
2. Realizar login do usuário
3. Consultar dados do usuário
4. Cadastrar gasto
5. Listar / consultar gastos (por id, por categoria, por período)
6. Atualizar gasto
7. Excluir gasto
8. Verificar limite de gastos do usuário
9. Cadastrar, listar, atualizar e excluir categorias
10. Cadastrar, listar, atualizar e excluir boletos, além de consultar boletos próximos do vencimento
11. Cadastrar, listar e excluir alertas do usuário, incluindo geração automática de alerta de limite
12. Gerar relatório financeiro do usuário
13. Gerar previsão financeira do usuário

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
