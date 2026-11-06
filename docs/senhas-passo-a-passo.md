# Correção 2 — senhas protegidas

1. **Cadastro:** usuario_service.py chama gerar_hash antes de salvar. A função
   usa scrypt do Werkzeug com salt aleatório. Senhas iguais produzem hashes
   diferentes. O hash cabe na coluna senha VARCHAR(255), sem alterar o esquema.
2. **Login:** conferir_senha verifica o hash. A senha original não é recuperada
   e o hash armazenado não é aceito como substituto da senha.
3. **Troca de senha:** uma nova senha recebe um novo hash. Atualizar só o nome
   preserva o hash atual. Senha vazia, nula, não textual ou acima de 1024
   caracteres é rejeitada. Não adicionamos exigências novas de complexidade
   nesta etapa, para preservar compatibilidade com as contas existentes.
4. **Contas antigas:** no primeiro login correto, o texto puro é substituído
   pelo hash. Uma tentativa incorreta não modifica o registro.
5. **Migração completa:** para não depender do próximo login, faça backup do
   banco, pare o servidor e execute `python migrar_senhas.py` com o .env do
   banco desejado. Depois reinicie o servidor. O script não chama setup_db.py,
   não recria tabelas e não imprime senhas. Executá-lo novamente não recalcula
   hashes já armazenados. Não foi executado no MySQL durante esta correção.
6. **Teste manual:** cadastre uma conta, entre, altere sua senha e saia. A senha
   antiga deve falhar e a nova deve funcionar. No banco, o campo deverá iniciar
   por `scrypt:32768:8:1$`, nunca pela senha original. Não compartilhe o hash.

Os prefixos `scrypt:` e `pbkdf2:` são reservados para hashes. Se uma senha antiga
em texto puro começar literalmente com um desses prefixos, ela não será tratada
como texto puro: essa conta exige redefinição controlada da senha. Isso evita
aceitar um hash malformado como credencial.

Validação automatizada: `python -m unittest discover -s tests -v`. Usa um banco
SQLite temporário; não valida a operação da migração em MySQL real.

Backups anteriores ainda podem conter texto puro. Hashing também não substitui
HTTPS, limites de tentativas ou a correção de XSS, que permanece pendente.
