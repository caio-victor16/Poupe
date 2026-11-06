# Correção 1 — autenticação e acesso aos próprios dados

## 1. Entenda a diferença

Antes, o navegador informava um ID e o servidor confiava nele. Agora o login
grava o ID numa sessão assinada pelo Flask. O cookie é HttpOnly: o JavaScript
não lê seu conteúdo. Alterar o localStorage não dá acesso a outra conta.
A sessão expira após oito horas. Ela é assinada, não criptografada; não guarde
senhas ou dados financeiros nela.

## 2. Configure a chave

Em desenvolvimento, uma chave aleatória é criada ao iniciar o processo.
Isso permite testar imediatamente, mas reiniciar encerra as sessões.
Para manter uma chave estável, gere um segredo com:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Copie o resultado para SECRET_KEY no seu .env. Não publique esse valor nem
o coloque no Git. Todos os processos do servidor precisam da mesma chave.
Em produção com HTTPS, configure também SESSION_COOKIE_SECURE=true.
Em HTTP local, mantenha false; caso contrário, o navegador não enviará o cookie.

## 3. Entenda a proteção central

backend/auth.py é executado antes dos controllers. Cadastro e login são públicos.
As demais APIs exigem uma sessão de um usuário que ainda exista no banco.
URLs com ID de usuário devem coincidir com a sessão. Gastos, boletos, alertas,
orçamentos e recorrências são consultados para conferir seu proprietário.
Na criação, o servidor define id_usuario a partir da sessão; um ID diferente
enviado pelo cliente é rejeitado.

Listagens globais de usuários, gastos e boletos foram bloqueadas. Use as rotas
por usuário. Categorias compartilhadas podem ser consultadas, mas sua alteração
pela API está bloqueada até existir um papel de administrador.
Ao criar rotas novas, revise explicitamente essa política.

## 4. Entenda a proteção das chamadas

O frontend usa a mesma origem do servidor e envia cookies. Requisições que
alteram dados precisam do cabeçalho X-Poupe-Request: 1. Sem CORS global, outro
site não recebe autorização do navegador para enviar esse cabeçalho.
SameSite=Strict é uma proteção adicional. Não reative CORS irrestrito.
Esse mecanismo não corrige XSS, que continua sendo uma próxima etapa.

Abra a interface pelo Flask, por exemplo http://127.0.0.1:5000, e não por
arquivo HTML ou Live Server. Evite alternar localhost e 127.0.0.1 durante o teste.

## 5. Teste manualmente

1. Faça login com uma conta de teste; consulte os próprios gastos.
2. Abra /usuarios/ID_DA_OUTRA_CONTA: deve retornar 403.
3. Clique em Sair; abra /sessao: deve retornar 401.
4. Em janela anônima, abra /gastos/usuario/1: deve retornar 401.
5. Faça login novamente: o uso normal deve voltar a funcionar.

O botão Sair agora chama POST /logout e remove o cookie da sessão no navegador.
Como a sessão padrão do Flask reside num cookie assinado, uma cópia roubada
anteriormente ainda pode valer até expirar. Revogação centralizada de sessões
exigiria armazenamento no servidor; não foi implementada nesta etapa.

## 6. Testes automatizados e limites

Com as dependências instaladas, execute:

```powershell
python -m unittest discover -s tests -v
```

Os testes usam SQLite em memória e não importam run.py nem executam setup_db.py.
Cobrem acesso anônimo em todas as rotas atuais, login/logout, isolamento dos
recursos, criação vinculada à sessão e proteção das chamadas entre origens.
Não validam procedures MySQL nem substituem um teste visual no navegador.

As senhas em texto puro, XSS e demais problemas do relatório ainda precisam ser
corrigidos nas próximas etapas. Não considere esta alteração uma auditoria
completa de segurança ou liberação para produção.

## Atualização (REV-002)

O cookie agora guarda também um token cujo hash fica na tabela `sessao_usuario`.
Logout e troca de senha apagam a sessão no banco, então um cookie copiado deixa
de valer. Detalhes em seguranca-acesso-passo-a-passo.md.
