# Correção 5 — erros sem detalhes internos e debug desativado por padrão

## 1. O que vazava

O tratamento geral em backend/__init__.py colocava str(erro) na resposta 500.
Uma exceção do banco pode conter consultas SQL, parâmetros e detalhes de
infraestrutura. Ela também era registrada integralmente no log.

## 2. Como a resposta funciona agora

Falhas inesperadas retornam uma mensagem fixa e um identificador aleatório:

```json
{
  "erro": "Erro interno no servidor. Tente novamente mais tarde.",
  "referencia": "identificador-gerado-para-essa-falha"
}
```

O log registra a mesma referência, o tipo da exceção e o nome da rota. Ele não
inclui o texto da exceção, SQL, parâmetros, corpo da requisição ou traceback.
Isso permite localizar o evento sem copiar dados privados. Diagnosticar a causa
completa pode exigir reproduzir o problema localmente com dados de teste.

Erros HTTP de servidor que chegarem ao tratamento geral também têm a descrição
ocultada. O status original é preservado, por exemplo 503. Cabeçalhos como
Retry-After e Allow continuam presentes. Mensagens intencionais de validação e
acesso negado continuam funcionando; não foram transformadas em erros 500.

## 3. Diferenciar mensagens públicas de falhas inesperadas na IA

A classe ErroIA identifica mensagens conhecidas, escritas para o usuário, como
um aviso de indisponibilidade do provedor. Um RuntimeError inesperado não é
mais devolvido integralmente ao navegador. Ao adicionar tratamentos novos,
nunca concatene uma exceção externa ou dados privados numa mensagem pública.

## 4. Configuração de desenvolvimento

No uso normal, mantenha no .env:

```dotenv
POUPE_DEBUG=false
```

Depois reinicie o servidor. Sem essa variável, o padrão também é false.
Para desenvolvimento local, POUPE_DEBUG=true ativa o modo debug do Flask.
Ao executar python run.py, o console interativo de depuração e o recarregamento
automático permanecem desligados, mesmo com essa opção. O servidor continua
escutando apenas em 127.0.0.1. Reinicie manualmente após editar arquivos.

Essas opções são do inicializador run.py. Um comando externo como flask run
--debug pode impor outra configuração. Não use o depurador em publicação.
Desligar debug não transforma o servidor de desenvolvimento em servidor de
produção.

## 5. CORS e frontend

O CORS global já estava desativado desde a primeira correção e continua assim.
Removi o objeto CORS não utilizado para evitar confusão. Abra frontend e API
pela mesma origem, por exemplo http://127.0.0.1:5000.

## 6. Verificação

Execute python -m unittest discover -s tests -v. Os testes provocam exceções
com dados fictícios sensíveis e conferem que esses dados não aparecem na
resposta nem no log do tratamento geral. Também verificam códigos HTTP,
cabeçalhos, CORS, configuração de debug e a inicialização sem console de
depuração. O banco é temporário e as chamadas à IA são simuladas.

Não adicione rotas que provocam erros ao aplicativo para testes manuais: as
rotas de teste existem apenas durante os testes automatizados. Nenhum log
antigo foi apagado; esta correção muda o comportamento dos novos eventos.
