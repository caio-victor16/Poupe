"""Contadores persistentes e atômicos, compartilhados pelos processos locais."""
import sqlite3
import time
from pathlib import Path
from contextlib import closing


def reservar_chamada(caminho, usuario_id, limites, agora=None):
    agora = int(time.time() if agora is None else agora)
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(caminho, timeout=5)) as conn, conn:
        conn.execute("CREATE TABLE IF NOT EXISTS limite (chave TEXT, janela INTEGER, "
                     "fim INTEGER, quantidade INTEGER NOT NULL, PRIMARY KEY(chave, janela))")
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("DELETE FROM limite WHERE fim <= ?", (agora,))
        baldes = []
        for nome, segundos, maximo, global_ in limites:
            chave = nome + (":global" if global_ else f":{usuario_id}")
            janela = agora // segundos
            fim = (janela + 1) * segundos
            linha = conn.execute("SELECT quantidade FROM limite WHERE chave=? AND janela=?",
                                 (chave, janela)).fetchone()
            if (linha[0] if linha else 0) >= maximo:
                return fim - agora
            baldes.append((chave, janela, fim))
        for chave, janela, fim in baldes:
            conn.execute("INSERT INTO limite VALUES (?, ?, ?, 1) "
                         "ON CONFLICT(chave, janela) DO UPDATE SET quantidade=quantidade+1",
                         (chave, janela, fim))
    return 0
