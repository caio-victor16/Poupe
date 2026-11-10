# setup_db.py
"""
Instala o schema do Poupe+ (tabelas, categorias e procedures) no banco
definido em MYSQL_DATABASE.

Uso:
    python setup_db.py                               # instala só se o banco não existir ou estiver vazio
    python setup_db.py --reset --confirmar NOME      # apaga e recria NOME (PERDE os dados!)
    python setup_db.py --atualizar                   # cria tabelas novas e recria procedures (dados intactos)
    python setup_db.py --atualizar-procedures        # recria só as procedures (dados intactos)

Regras de segurança:
- O nome do banco vem somente do .env e é validado; o poupe.sql não escolhe
  nem apaga bancos (DROP DATABASE/SCHEMA no script interrompe a instalação).
- Banco vazio ou inexistente: instala.
- Banco com todas as tabelas e procedures do Poupe+: não faz nada.
- Qualquer outro estado (instalação parcial, tabelas de outro sistema):
  não altera nada e explica o que fazer.
- --reset só apaga o banco configurado, e só com --confirmar igual ao nome dele.
- --atualizar só roda em banco que já tem tabelas do Poupe+: cria as tabelas
  que faltam, acrescenta as colunas novas listadas em COLUNAS_NOVAS (sem apagar
  nada) e recria as procedures.
- --atualizar-procedures só roda em banco com todas as tabelas do Poupe+ e
  só recria procedures; não altera tabelas nem dados.
"""
import argparse
import contextlib
import os
import re
import sys

import pymysql
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("MYSQL_HOST", "localhost")
PORT = int(os.getenv("MYSQL_PORT", "3306"))
USER = os.getenv("MYSQL_USER", "root")
PASSWORD = os.getenv("MYSQL_PASSWORD", "")
DATABASE = os.getenv("MYSQL_DATABASE", "poupe")
SQL_FILE = os.path.join(os.path.dirname(__file__), "database", "mysql", "poupe.sql")
LOCK_TIMEOUT = 30  # segundos esperando outro processo terminar a instalação

NOME_VALIDO = re.compile(r"[A-Za-z0-9_]{1,64}")
COMANDO_PROIBIDO = re.compile(r"\s*drop\s+(database|schema)\b", re.IGNORECASE)
COMANDO_DE_BANCO = re.compile(r"\s*(create\s+(database|schema)\b|use\s)", re.IGNORECASE)
CREATE_TABLE = re.compile(r"\s*create\s+table\s+(?:if\s+not\s+exists\s+)?`?(\w+)`?", re.IGNORECASE)
INSERT_INTO = re.compile(r"\s*insert\s+into\s+`?(\w+)`?", re.IGNORECASE)
CREATE_PROCEDURE = re.compile(r"\s*create\s+procedure\s+(?:if\s+not\s+exists\s+)?`?(\w+)`?", re.IGNORECASE)


class ErroInstalacao(RuntimeError):
    """Instalação recusada ou interrompida; a mensagem é segura para exibir."""


def ler_comandos(caminho):
    """Lê o .sql respeitando o DELIMITER das procedures."""
    delimitador = ";"
    buffer = []
    comandos = []
    with open(caminho, encoding="utf-8") as arquivo:
        for linha in arquivo:
            texto = linha.strip()
            if not texto or texto.startswith("--"):
                continue
            if texto.lower().startswith("delimiter"):
                delimitador = texto.split()[1]
                continue
            buffer.append(linha)
            if texto.endswith(delimitador):
                comando = "".join(buffer).strip()[: -len(delimitador)].strip()
                if comando:
                    comandos.append(comando)
                buffer = []
    return comandos


def validar_nome(nome):
    if not isinstance(nome, str) or not NOME_VALIDO.fullmatch(nome):
        raise ErroInstalacao(
            "MYSQL_DATABASE inválido. Use apenas letras sem acento, números e _ "
            "(até 64 caracteres)."
        )
    return nome


def preparar_comandos(caminho=SQL_FILE):
    """Comandos do schema, sem os que escolhem ou criam o banco."""
    comandos = []
    for comando in ler_comandos(caminho):
        if COMANDO_PROIBIDO.match(comando):
            raise ErroInstalacao(
                "poupe.sql contém DROP DATABASE/SCHEMA. O instalador não executa "
                "scripts que apagam bancos; use --reset --confirmar."
            )
        if COMANDO_DE_BANCO.match(comando):
            continue  # o banco é sempre o de MYSQL_DATABASE, criado pelo instalador
        comandos.append(comando)
    return comandos


# Colunas acrescentadas depois em tabelas que já existiam (o CREATE TABLE do
# poupe.sql já as tem; isto é só para bancos de versões anteriores).
# (tabela, coluna, comando que acrescenta)
COLUNAS_NOVAS = [
    ("usuario", "termos_aceitos_em", "ALTER TABLE usuario ADD COLUMN termos_aceitos_em datetime NULL"),
    ("usuario", "termos_versao", "ALTER TABLE usuario ADD COLUMN termos_versao varchar(20) NULL"),
    ("boleto", "descricao", "ALTER TABLE boleto ADD COLUMN descricao varchar(100) NOT NULL DEFAULT ''"),
    ("boleto", "id_categoria", "ALTER TABLE boleto ADD COLUMN id_categoria int NULL, "
     "ADD CONSTRAINT fk_boleto_categoria FOREIGN KEY (id_categoria) REFERENCES categoria(id_categoria)"),
    ("boleto", "fixo", "ALTER TABLE boleto ADD COLUMN fixo boolean NOT NULL DEFAULT false"),
    ("boleto", "debito_automatico",
     "ALTER TABLE boleto ADD COLUMN debito_automatico boolean NOT NULL DEFAULT false"),
    ("boleto", "dia_vencimento", "ALTER TABLE boleto ADD COLUMN dia_vencimento int NULL"),
    ("boleto", "data_pagamento", "ALTER TABLE boleto ADD COLUMN data_pagamento date NULL"),
    ("boleto", "id_gasto", "ALTER TABLE boleto ADD COLUMN id_gasto int NULL, "
     "ADD CONSTRAINT fk_boleto_gasto FOREIGN KEY (id_gasto) REFERENCES gasto(id_gasto) ON DELETE SET NULL"),
]
# Colunas que deixaram de ser obrigatórias: (tabela, coluna, comando).
COLUNAS_OPCIONAIS = [
    ("boleto", "codigo_barras", "ALTER TABLE boleto MODIFY codigo_barras varchar(100) NULL"),
]
# Ao ganhar as colunas novas, os gastos fixos (recorrências mensais ativas) viram
# boletos fixos com débito automático, mantendo o comportamento de antes
# (lançar o gasto sozinho no vencimento). A recorrência antiga é desativada.
CONVERTER_RECORRENCIAS = [
    """INSERT INTO boleto (id_usuario, descricao, id_categoria, codigo_barras, valor, vencimento,
                          status, fixo, debito_automatico, dia_vencimento)
       SELECT r.id_usuario, LEFT(COALESCE(NULLIF(TRIM(r.descricao), ''), c.nome), 100),
              r.id_categoria, NULL, r.valor, r.proxima_data, 'pendente', true, true, r.dia_mes
       FROM recorrencia_gasto r JOIN categoria c ON c.id_categoria = r.id_categoria
       WHERE r.ativa = true AND r.frequencia = 'mensal'""",
    "UPDATE recorrencia_gasto SET ativa = false WHERE ativa = true AND frequencia = 'mensal'",
]


def migracoes_pendentes(conn, nome, existentes):
    """[(rótulo, comando)] das colunas novas/opcionais ainda não aplicadas, só
    em tabelas que já existem (tabela criada agora já vem completa)."""
    tabelas = {t for t, _, _ in COLUNAS_NOVAS + COLUNAS_OPCIONAIS} & existentes
    if not tabelas:
        return []
    with conn.cursor() as cur:
        cur.execute(
            "SELECT table_name, column_name, is_nullable FROM information_schema.columns "
            "WHERE table_schema = %s AND table_name IN ("
            + ", ".join(["%s"] * len(tabelas)) + ")",
            (nome, *sorted(tabelas)),
        )
        colunas = {(t.lower(), c.lower()): n for t, c, n in cur.fetchall()}
    pendentes = [(f"{t}.{c}", sql) for t, c, sql in COLUNAS_NOVAS
                 if t in tabelas and (t, c) not in colunas]
    pendentes += [(f"{t}.{c} (opcional)", sql) for t, c, sql in COLUNAS_OPCIONAIS
                  if t in tabelas and colunas.get((t, c), "YES") == "NO"]
    return pendentes


def objetos_esperados(comandos):
    tabelas, procedures = set(), set()
    for comando in comandos:
        if m := CREATE_TABLE.match(comando):
            tabelas.add(m.group(1).lower())
        elif m := CREATE_PROCEDURE.match(comando):
            procedures.add(m.group(1).lower())
    if not tabelas:
        raise ErroInstalacao("poupe.sql não contém nenhuma tabela.")
    return tabelas, procedures


def objetos_existentes(conn, nome):
    """(existe, tabelas, rotinas) do banco, com nomes em minúsculas."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = %s",
            (nome,),
        )
        if cur.fetchone()[0] == 0:
            return False, set(), set()
        cur.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = %s",
            (nome,),
        )
        existentes = {linha[0].lower() for linha in cur.fetchall()}
        cur.execute(
            "SELECT routine_name FROM information_schema.routines "
            "WHERE routine_schema = %s",
            (nome,),
        )
        rotinas = {linha[0].lower() for linha in cur.fetchall()}
    return True, existentes, rotinas


def estado_banco(conn, nome, tabelas, procedures):
    """Retorna ('ausente'|'vazio'|'completo'|'parcial'|'estranho', faltando)."""
    existe, existentes, rotinas = objetos_existentes(conn, nome)
    if not existe:
        return "ausente", set()
    if not existentes and not rotinas:
        return "vazio", set()
    faltando = (tabelas - existentes) | (procedures - rotinas)
    faltando |= {rotulo for rotulo, _ in migracoes_pendentes(conn, nome, existentes & tabelas)}
    if not faltando:
        return "completo", set()
    if not (existentes & tabelas):
        return "estranho", faltando
    return "parcial", faltando


def conectar():
    try:
        return pymysql.connect(
            host=HOST, port=PORT, user=USER, password=PASSWORD,
            charset="utf8mb4", autocommit=True,
        )
    except pymysql.MySQLError as erro:
        raise ErroInstalacao(
            f"Não foi possível conectar ao MySQL em {HOST}:{PORT} "
            f"(erro {erro.args[0] if erro.args else '?'}). Verifique o .env."
        ) from erro


def instalar(conn, nome, comandos):
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{nome}` CHARACTER SET utf8mb4")
        conn.select_db(nome)
        for comando in comandos:
            try:
                cur.execute(comando)
            except pymysql.MySQLError as erro:
                raise ErroInstalacao(
                    f"Falha ao instalar o banco '{nome}' (erro "
                    f"{erro.args[0] if erro.args else '?'}). Ele pode ter ficado "
                    "incompleto; nada foi apagado. Corrija a causa e recrie com "
                    f"python setup_db.py --reset --confirmar {nome}"
                ) from erro


@contextlib.contextmanager
def travado(conn, nome):
    """Evita duas instalações/atualizações simultâneas do mesmo banco."""
    trava = f"poupe_setup:{nome}"
    with conn.cursor() as cur:
        cur.execute("SELECT GET_LOCK(%s, %s)", (trava, LOCK_TIMEOUT))
        if cur.fetchone()[0] != 1:
            raise ErroInstalacao("Outra instalação do banco está em andamento.")
    try:
        yield
    finally:
        with conn.cursor() as cur:
            cur.execute("SELECT RELEASE_LOCK(%s)", (trava,))


def criar_banco(forcar=False, confirmacao=None):
    """Retorna True se instalou o banco, False se ele já estava completo.

    Lança ErroInstalacao quando recusa agir; nesse caso nada foi alterado.
    """
    nome = validar_nome(DATABASE)
    comandos = preparar_comandos(SQL_FILE)
    tabelas, procedures = objetos_esperados(comandos)
    if forcar and confirmacao != nome:
        raise ErroInstalacao(
            f"--reset apaga TODOS os dados de '{nome}'. Para confirmar, rode: "
            f"python setup_db.py --reset --confirmar {nome}"
        )

    conn = conectar()
    try:
        with travado(conn, nome):
            if forcar:
                with conn.cursor() as cur:
                    cur.execute(f"DROP DATABASE IF EXISTS `{nome}`")
            else:
                estado, faltando = estado_banco(conn, nome, tabelas, procedures)
                if estado == "completo":
                    return False
                if estado in ("parcial", "estranho"):
                    lista = ", ".join(sorted(faltando))
                    motivo = (
                        "tem tabelas que não são do Poupe+"
                        if estado == "estranho"
                        else "está incompleto ou é de uma versão anterior do Poupe+"
                    )
                    if estado == "parcial":
                        raise ErroInstalacao(
                            f"O banco '{nome}' {motivo} (faltam: {lista}). Nada foi "
                            "alterado. Se for uma versão anterior do Poupe+, rode "
                            "python setup_db.py --atualizar (cria só o que falta, "
                            "sem apagar dados). Confira antes MYSQL_DATABASE no .env."
                        )
                    raise ErroInstalacao(
                        f"O banco '{nome}' já existe e {motivo} (faltam: {lista}). "
                        "Nada foi alterado. Confira MYSQL_DATABASE no .env; se for "
                        "mesmo o banco do Poupe+, faça backup e rode "
                        f"python setup_db.py --reset --confirmar {nome}"
                    )
            instalar(conn, nome, comandos)
            return True
    finally:
        conn.close()


def _recriar_procedures(conn, criacoes):
    with conn.cursor() as cur:
        for procedure, comando in criacoes:
            try:
                cur.execute(f"DROP PROCEDURE IF EXISTS `{procedure}`")
                cur.execute(comando)
            except pymysql.MySQLError as erro:
                raise ErroInstalacao(
                    f"Falha ao recriar {procedure} (erro "
                    f"{erro.args[0] if erro.args else '?'}). Tabelas e dados "
                    "não foram alterados; corrija e rode de novo."
                ) from erro


def _aplicar_migracoes(conn, nome, existentes):
    """Acrescenta colunas novas; se o boleto ganhou as colunas agora, converte as
    recorrências mensais em boletos fixos. Retorna a lista do que foi feito."""
    feitas = []
    pendentes = migracoes_pendentes(conn, nome, existentes)
    with conn.cursor() as cur:
        try:
            for rotulo, comando in pendentes:
                cur.execute(comando)
                feitas.append(rotulo)
            if "boleto.fixo" in feitas and "recorrencia_gasto" in existentes:
                cur.execute(CONVERTER_RECORRENCIAS[0])
                convertidas = cur.rowcount
                cur.execute(CONVERTER_RECORRENCIAS[1])
                feitas.append(f"{convertidas} gasto(s) fixo(s) convertido(s) em boletos fixos")
        except pymysql.MySQLError as erro:
            raise ErroInstalacao(
                f"Falha ao atualizar colunas (erro {erro.args[0] if erro.args else '?'}). "
                f"Já aplicado: {', '.join(feitas) or 'nada'}. Dados não foram apagados; "
                "corrija e rode --atualizar de novo (ele continua de onde parou)."
            ) from erro
    return feitas


def atualizar_banco():
    """Atualiza um banco do Poupe+ de versão anterior sem apagar dados.

    Cria só as tabelas do poupe.sql que ainda não existem (com os dados
    iniciais delas, se houver) e recria as procedures. Retorna
    (tabelas_criadas, quantidade_de_procedures).
    """
    nome = validar_nome(DATABASE)
    comandos = preparar_comandos(SQL_FILE)
    tabelas, _ = objetos_esperados(comandos)
    criacoes = [(CREATE_PROCEDURE.match(c).group(1), c)
                for c in comandos if CREATE_PROCEDURE.match(c)]

    conn = conectar()
    try:
        with travado(conn, nome):
            existe, existentes, _ = objetos_existentes(conn, nome)
            if not existe or "usuario" not in existentes or not (existentes & tabelas):
                raise ErroInstalacao(
                    f"O banco '{nome}' não parece ser do Poupe+ (sem a tabela usuario). "
                    "Nada foi alterado. Para instalar do zero, rode python setup_db.py"
                )
            conn.select_db(nome)
            criadas = []
            with conn.cursor() as cur:
                for comando in comandos:
                    tabela = CREATE_TABLE.match(comando)
                    insercao = INSERT_INTO.match(comando)
                    try:
                        if tabela and tabela.group(1).lower() not in existentes:
                            cur.execute(comando)
                            criadas.append(tabela.group(1).lower())
                        elif insercao and insercao.group(1).lower() in criadas:
                            cur.execute(comando)   # dados iniciais só de tabela nova
                    except pymysql.MySQLError as erro:
                        raise ErroInstalacao(
                            f"Falha ao criar tabelas novas (erro "
                            f"{erro.args[0] if erro.args else '?'}). Tabelas já "
                            f"existentes não foram alteradas. Criadas até aqui: "
                            f"{', '.join(criadas) or 'nenhuma'}."
                        ) from erro
            criadas += _aplicar_migracoes(conn, nome, existentes)
            _recriar_procedures(conn, criacoes)
            return criadas, len(criacoes)
    finally:
        conn.close()


def atualizar_procedures():
    """Recria as procedures do poupe.sql num banco do Poupe+ já instalado.

    Retorna a quantidade recriada. Não altera tabelas nem dados.
    """
    nome = validar_nome(DATABASE)
    comandos = preparar_comandos(SQL_FILE)
    tabelas, _ = objetos_esperados(comandos)
    criacoes = [(CREATE_PROCEDURE.match(c).group(1), c)
                for c in comandos if CREATE_PROCEDURE.match(c)]

    conn = conectar()
    try:
        with travado(conn, nome):
            existe, existentes, _ = objetos_existentes(conn, nome)
            faltando = tabelas - existentes
            if not existe or faltando:
                raise ErroInstalacao(
                    f"O banco '{nome}' não tem todas as tabelas do Poupe+"
                    + (f" (faltam: {', '.join(sorted(faltando))})" if existe else " (não existe)")
                    + ". Nada foi alterado. Para instalar, rode python setup_db.py;"
                    " para atualizar uma versão anterior, python setup_db.py --atualizar"
                )
            conn.select_db(nome)
            _recriar_procedures(conn, criacoes)
            return len(criacoes)
    finally:
        conn.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Instala o banco do Poupe+.")
    parser.add_argument("--reset", action="store_true",
                        help="apaga e recria o banco configurado (PERDE os dados)")
    parser.add_argument("--confirmar", metavar="NOME",
                        help="nome do banco, obrigatório junto com --reset")
    parser.add_argument("--atualizar", action="store_true",
                        help="cria tabelas novas e recria procedures (sem apagar dados)")
    parser.add_argument("--atualizar-procedures", action="store_true",
                        help="recria só as procedures num banco já instalado")
    args = parser.parse_args(argv)
    if sum([args.reset, args.atualizar, args.atualizar_procedures]) > 1:
        parser.error("use só uma opção: --reset, --atualizar ou --atualizar-procedures")
    if args.atualizar:
        try:
            criadas, quantidade = atualizar_banco()
        except ErroInstalacao as erro:
            print(f"Erro: {erro}", file=sys.stderr)
            return 1
        novas = ", ".join(criadas) if criadas else "nada (já estava tudo)"
        print(f"Banco '{DATABASE}' atualizado. Criado/alterado: {novas}. "
              f"Procedures recriadas: {quantidade}. Dados intactos.")
        return 0
    if args.atualizar_procedures:
        try:
            quantidade = atualizar_procedures()
        except ErroInstalacao as erro:
            print(f"Erro: {erro}", file=sys.stderr)
            return 1
        print(f"{quantidade} procedures atualizadas em '{DATABASE}'. Dados intactos.")
        return 0
    try:
        criado = criar_banco(forcar=args.reset, confirmacao=args.confirmar)
    except ErroInstalacao as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    if criado:
        print(f"Banco '{DATABASE}' criado com sucesso!")
    else:
        print(f"Banco '{DATABASE}' já está instalado. Nada foi alterado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
