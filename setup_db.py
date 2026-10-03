# setup_db.py
"""
Cria o banco 'poupe' (tabelas, categorias e procedures) automaticamente.
Uso:
    python setup_db.py            # cria só se ainda não existir
    python setup_db.py --reset    # apaga e recria tudo (PERDE os dados!)
"""
import os
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


def banco_pronto(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = %s AND table_name = 'usuario'",
            (DATABASE,),
        )
        return cur.fetchone()[0] > 0


def criar_banco(forcar=False):
    """Retorna True se criou o banco, False se ele já existia."""
    conn = pymysql.connect(
        host=HOST, port=PORT, user=USER, password=PASSWORD,
        charset="utf8mb4", autocommit=True,
    )
    try:
        if banco_pronto(conn) and not forcar:
            return False
        with conn.cursor() as cur:
            for comando in ler_comandos(SQL_FILE):
                cur.execute(comando)
        return True
    finally:
        conn.close()


if __name__ == "__main__":
    if criar_banco(forcar="--reset" in sys.argv):
        print("Banco 'poupe' criado com sucesso!")
    else:
        print("Banco 'poupe' já existe. Use --reset para recriar (apaga os dados).")