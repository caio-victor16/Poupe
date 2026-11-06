# Correção 6 — instalação do banco sem apagar dados

## 1. O problema

- `poupe.sql` começava com `drop database if exists poupe`.
- `setup_db.py` verificava se existia a tabela `usuario` no banco de
  `MYSQL_DATABASE`, mas o script sempre apagava o banco chamado `poupe`.
  Com `MYSQL_DATABASE=outro_nome`, a verificação olhava um banco e o
  `DROP` atingia outro: o banco `poupe` real podia ser apagado.
- Uma única tabela não comprova instalação completa.
- `run.py` chamava `criar_banco()` ao ser **importado** (por exemplo, por
  `flask --app run` ou por um teste), não só ao ser executado.

## 2. Como funciona agora

1. O nome do banco vem só de `MYSQL_DATABASE` e é validado
   (`[A-Za-z0-9_]`, até 64 caracteres) antes de qualquer conexão.
2. `poupe.sql` não apaga bancos. As linhas `create database`/`use` do
   script são ignoradas pelo instalador, que cria e seleciona o banco
   configurado. Se alguém recolocar `DROP DATABASE` no script, o
   instalador recusa executá-lo.
3. O instalador lê do próprio `poupe.sql` a lista de tabelas e procedures
   e compara com o banco:

   | Estado do banco | Ação |
   |---|---|
   | Não existe ou vazio | Instala |
   | Tem todas as tabelas e procedures | Não faz nada |
   | Instalação incompleta | Recusa, lista o que falta, não altera nada |
   | Tabelas de outro sistema | Recusa, não altera nada |

4. `GET_LOCK` impede dois processos de instalarem ao mesmo tempo.
5. `--reset` exige confirmar o nome do banco:
   `python setup_db.py --reset --confirmar poupe`. Sem a confirmação
   correta, nem conecta ao MySQL. Só apaga o banco configurado.
6. `run.py` só verifica o banco dentro de `main()`. Se o instalador
   recusar, o servidor não sobe e mostra o motivo (código de saída 1).

## 3. Atualizando um banco antigo

Se o servidor disser que o banco está incompleto, confira primeiro se
`MYSQL_DATABASE` no `.env` aponta para o banco certo. Se sim, faça backup
(`mysqldump`) e rode o reset com confirmação. Não há migração automática
que preserve dados de versões antigas.

## 4. Limites

- O instalador confere a existência das tabelas/procedures, não suas
  colunas. Um banco com a estrutura antiga, mas com os mesmos nomes, é
  considerado completo.
- DDL do MySQL não é transacional: uma falha no meio da instalação deixa
  o banco parcial. Na próxima execução ele será recusado (não apagado), e
  a mensagem indica o reset.
- O usuário do MySQL continua sendo o de `.env` (padrão `root`). Usar um
  usuário com privilégios restritos ao banco do Poupe+ reduz o impacto
  de erros de configuração.
- `poupe.sql` executado manualmente no Workbench usa o nome `poupe`
  escrito no arquivo; em banco já instalado ele falha no primeiro
  `create table`, sem apagar dados.

## 5. Testes

- `tests/test_setup_db.py`: conexão simulada; cobre nome inválido, script
  com DROP, banco ausente/vazio/completo/parcial/estranho, trava
  concorrente e reset com e sem confirmação.
- `tests/test_errors.py`: importar `run.py` não toca no banco; recusa do
  instalador impede a subida do servidor.
- Validação manual em MariaDB 10.11 descrita no `CONTEXTO_DO_PROJETO.md`.
