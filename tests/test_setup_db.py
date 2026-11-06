"""Instalador do banco: nunca apaga nem altera um banco existente sem confirmação.

Nenhum teste conecta ao MySQL: a conexão é substituída por um objeto falso
que registra os comandos executados.
"""
import io
import re
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

import setup_db

ROOT = Path(__file__).resolve().parents[1]
SQL_REAL = ROOT / 'database' / 'mysql' / 'poupe.sql'


class CursorFalso:
    def __init__(self, conn):
        self.conn = conn
        self.resultado = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, params=None):
        self.conn.executados.append(sql)
        texto = sql.lower()
        if 'information_schema.schemata' in texto:
            self.resultado = [(1 if self.conn.existe else 0,)]
        elif 'information_schema.tables' in texto:
            self.resultado = [(t,) for t in self.conn.tabelas]
        elif 'information_schema.routines' in texto:
            self.resultado = [(r,) for r in self.conn.rotinas]
        elif 'get_lock' in texto:
            self.resultado = [(self.conn.lock,)]
        else:
            self.resultado = [(1,)]

    def fetchone(self):
        return self.resultado[0]

    def fetchall(self):
        return self.resultado


class ConexaoFalsa:
    def __init__(self, existe=False, tabelas=(), rotinas=(), lock=1):
        self.existe, self.tabelas, self.rotinas, self.lock = existe, list(tabelas), list(rotinas), lock
        self.executados, self.selecionado, self.fechada = [], None, False

    def cursor(self):
        return CursorFalso(self)

    def select_db(self, nome):
        self.selecionado = nome

    def close(self):
        self.fechada = True

    def ddl(self):
        """Comandos que alteram algo (ignora consultas e travas)."""
        return [c for c in self.executados
                if not c.lstrip().upper().startswith('SELECT')]


COMANDOS = setup_db.preparar_comandos(str(SQL_REAL))
TABELAS, PROCEDURES = setup_db.objetos_esperados(COMANDOS)


class SetupDbTest(unittest.TestCase):
    def rodar(self, conn, nome='poupe_teste', **kwargs):
        with patch.object(setup_db, 'DATABASE', nome), \
                patch.object(setup_db.pymysql, 'connect', return_value=conn) as connect:
            resultado = setup_db.criar_banco(**kwargs)
        return resultado, connect

    # --- script SQL -------------------------------------------------------

    def test_real_script_never_drops_and_lists_all_objects(self):
        texto = SQL_REAL.read_text(encoding='utf-8')
        comandos = setup_db.ler_comandos(str(SQL_REAL))
        self.assertFalse(any(setup_db.COMANDO_PROIBIDO.match(c) for c in comandos))
        self.assertNotRegex(texto.lower(), r'^\s*drop\s+(database|schema)', )
        self.assertFalse(any(setup_db.COMANDO_DE_BANCO.match(c) for c in COMANDOS))
        self.assertEqual(TABELAS, {
            'usuario', 'categoria', 'gasto', 'boleto', 'alerta', 'previsao_financeira',
            'extrato', 'orcamento_categoria', 'recorrencia_gasto', 'receita',
            'receita_recorrente', 'conta', 'meta', 'cofrinho',
            'sessao_usuario', 'tentativa_acesso'})
        self.assertEqual(len(PROCEDURES), 7)

    def test_script_with_drop_database_is_refused(self):
        with tempfile.TemporaryDirectory() as pasta:
            sql = Path(pasta) / 'x.sql'
            sql.write_text('DROP DATABASE IF EXISTS outro;\ncreate table t (id int);\n', encoding='utf-8')
            with self.assertRaises(setup_db.ErroInstalacao):
                setup_db.preparar_comandos(str(sql))

    def test_invalid_database_names_are_refused_before_connecting(self):
        for nome in ('', 'poupe`; drop database x; --', 'meu banco', 'a' * 65, 'poupe.x'):
            conn = ConexaoFalsa()
            with self.assertRaises(setup_db.ErroInstalacao):
                _, connect = self.rodar(conn, nome=nome)
            self.assertEqual(conn.executados, [])

    # --- estados do banco ---------------------------------------------------

    def test_missing_database_is_created_with_configured_name(self):
        conn = ConexaoFalsa(existe=False)
        criado, _ = self.rodar(conn)
        self.assertTrue(criado)
        ddl = conn.ddl()
        self.assertEqual(ddl[0], 'CREATE DATABASE IF NOT EXISTS `poupe_teste` CHARACTER SET utf8mb4')
        self.assertEqual(conn.selecionado, 'poupe_teste')
        self.assertEqual(ddl[1:], COMANDOS)
        self.assertFalse(any('drop' in c.lower().split('(')[0] for c in ddl))
        self.assertTrue(conn.fechada)
        self.assertIn('RELEASE_LOCK', conn.executados[-1])

    def test_empty_database_is_installed(self):
        conn = ConexaoFalsa(existe=True)
        criado, _ = self.rodar(conn)
        self.assertTrue(criado)

    def test_complete_database_is_left_untouched(self):
        conn = ConexaoFalsa(existe=True, tabelas=[t.upper() for t in TABELAS] + ['extra'],
                            rotinas=PROCEDURES)
        criado, _ = self.rodar(conn)
        self.assertFalse(criado)
        self.assertEqual(conn.ddl(), [])

    def test_partial_installation_is_refused_without_changes(self):
        # Antes: bastava existir "usuario" para considerar o banco pronto.
        for tabelas, rotinas in ((['usuario'], []), (TABELAS, [])):
            conn = ConexaoFalsa(existe=True, tabelas=tabelas, rotinas=rotinas)
            with self.assertRaises(setup_db.ErroInstalacao) as erro:
                self.rodar(conn)
            self.assertIn('versão anterior', str(erro.exception))
            self.assertIn('--atualizar', str(erro.exception))
            self.assertEqual(conn.ddl(), [])
            self.assertTrue(conn.fechada)

    def test_foreign_database_is_refused_without_changes(self):
        conn = ConexaoFalsa(existe=True, tabelas=['clientes', 'pedidos'])
        with self.assertRaises(setup_db.ErroInstalacao) as erro:
            self.rodar(conn, nome='loja')
        self.assertIn('não são do Poupe+', str(erro.exception))
        self.assertEqual(conn.ddl(), [])

    def test_concurrent_installation_waits_and_gives_up_safely(self):
        conn = ConexaoFalsa(existe=False, lock=0)
        with self.assertRaises(setup_db.ErroInstalacao):
            self.rodar(conn)
        self.assertEqual(conn.ddl(), [])

    # --- reset ----------------------------------------------------------------

    def test_reset_requires_matching_confirmation_before_connecting(self):
        for confirmacao in (None, '', 'poupe', 'POUPE_TESTE'):
            conn = ConexaoFalsa(existe=True, tabelas=TABELAS, rotinas=PROCEDURES)
            with self.assertRaises(setup_db.ErroInstalacao):
                _, connect = self.rodar(conn, forcar=True, confirmacao=confirmacao)
            self.assertEqual(conn.executados, [])

    def test_confirmed_reset_drops_only_configured_database(self):
        conn = ConexaoFalsa(existe=True, tabelas=TABELAS, rotinas=PROCEDURES)
        criado, _ = self.rodar(conn, forcar=True, confirmacao='poupe_teste')
        self.assertTrue(criado)
        drops = [c for c in conn.ddl() if c.upper().startswith('DROP')]
        self.assertEqual(drops, ['DROP DATABASE IF EXISTS `poupe_teste`'])

    def test_cli_reset_without_confirmation_exits_with_error(self):
        conn = ConexaoFalsa(existe=True, tabelas=TABELAS, rotinas=PROCEDURES)
        stderr = io.StringIO()
        with patch.object(setup_db, 'DATABASE', 'poupe'), \
                patch.object(setup_db.pymysql, 'connect', return_value=conn), redirect_stderr(stderr):
            codigo = setup_db.main(['--reset'])
        self.assertEqual(codigo, 1)
        self.assertIn('--confirmar poupe', stderr.getvalue())
        self.assertEqual(conn.executados, [])


    # --- atualizar procedures (item 9) -----------------------------------------

    def test_update_procedures_recreates_only_procedures(self):
        conn = ConexaoFalsa(existe=True, tabelas=TABELAS, rotinas=PROCEDURES)
        with patch.object(setup_db, 'DATABASE', 'poupe_teste'), \
                patch.object(setup_db.pymysql, 'connect', return_value=conn):
            quantidade = setup_db.atualizar_procedures()
        self.assertEqual(quantidade, len(PROCEDURES))
        self.assertEqual(conn.selecionado, 'poupe_teste')
        ddl = conn.ddl()
        drops = [c for c in ddl if c.upper().startswith('DROP')]
        self.assertEqual(len(drops), len(PROCEDURES))
        self.assertTrue(all(c.startswith('DROP PROCEDURE IF EXISTS `') for c in drops))
        for comando in ddl:
            self.assertRegex(comando.lower(), r'^\s*(drop procedure if exists|create procedure)')
        self.assertIn('RELEASE_LOCK', conn.executados[-1])

    def test_update_procedures_refuses_incomplete_or_missing_database(self):
        for conn in (ConexaoFalsa(existe=False),
                     ConexaoFalsa(existe=True, tabelas=['usuario'])):
            with patch.object(setup_db, 'DATABASE', 'poupe_teste'), \
                    patch.object(setup_db.pymysql, 'connect', return_value=conn):
                with self.assertRaises(setup_db.ErroInstalacao):
                    setup_db.atualizar_procedures()
            self.assertEqual(conn.ddl(), [])

    def test_limit_procedures_only_count_current_month(self):
        procedures = {setup_db.CREATE_PROCEDURE.match(c).group(1): c.lower()
                      for c in COMANDOS if setup_db.CREATE_PROCEDURE.match(c)}
        filtro_inicio = "data >= date_format(curdate(), '%y-%m-01')"
        filtro_fim = "data <  date_add(date_format(curdate(), '%y-%m-01'), interval 1 month)"
        self.assertIn(filtro_inicio, procedures['sp_verificar_limite_gastos'])
        self.assertIn(filtro_fim, procedures['sp_verificar_limite_gastos'])
        # sp_gerar_alerta_limite guarda o início do mês numa variável (item 14).
        alerta = procedures['sp_gerar_alerta_limite']
        self.assertIn("v_inicio_mes date default date_format(curdate(), '%y-%m-01')", alerta)
        self.assertIn("data >= v_inicio_mes", alerta)
        self.assertIn("data <  date_add(v_inicio_mes, interval 1 month)", alerta)

    def test_limit_alert_is_not_duplicated_within_the_month(self):
        procedures = {setup_db.CREATE_PROCEDURE.match(c).group(1): c.lower()
                      for c in COMANDOS if setup_db.CREATE_PROCEDURE.match(c)}
        alerta = procedures['sp_gerar_alerta_limite']
        self.assertEqual(alerta.count('insert into alerta'), 1)
        self.assertIn('where not exists', alerta)
        self.assertIn('get_lock(v_trava', alerta)
        self.assertIn('release_lock(v_trava)', alerta)
        self.assertIn('nullif(u.limite_gastos, 0)', procedures['sp_verificar_limite_gastos'])


    # --- atualizar banco de versão anterior (item 10c) --------------------------

    def atualizar(self, conn, nome='poupe_teste'):
        with patch.object(setup_db, 'DATABASE', nome), \
                patch.object(setup_db.pymysql, 'connect', return_value=conn):
            return setup_db.atualizar_banco()

    def test_update_creates_only_missing_tables_and_keeps_existing(self):
        antigas = TABELAS - {'receita'}
        conn = ConexaoFalsa(existe=True, tabelas=antigas, rotinas=PROCEDURES)
        criadas, procedures = self.atualizar(conn)
        self.assertEqual(criadas, ['receita'])
        self.assertEqual(procedures, len(PROCEDURES))
        ddl = conn.ddl()
        creates = [c for c in ddl if c.lower().lstrip().startswith('create table')]
        self.assertEqual(len(creates), 1)
        self.assertRegex(creates[0].lower(), r'create table receita')
        self.assertFalse(any(c.lower().lstrip().startswith('insert') for c in ddl))   # categoria já existia
        self.assertFalse(any(re.match(r'\s*(drop\s+table|alter|delete|truncate)', c, re.I) for c in ddl))
        self.assertIn('RELEASE_LOCK', conn.executados[-1])

    def test_update_seeds_only_tables_it_created(self):
        conn = ConexaoFalsa(existe=True, tabelas=['usuario', 'gasto'])
        criadas, _ = self.atualizar(conn)
        self.assertIn('categoria', criadas)
        inserts = [c for c in conn.ddl() if c.lower().lstrip().startswith('insert')]
        self.assertTrue(inserts and all('categoria' in c.lower() for c in inserts))

    def test_update_on_complete_database_creates_nothing(self):
        conn = ConexaoFalsa(existe=True, tabelas=TABELAS, rotinas=PROCEDURES)
        criadas, _ = self.atualizar(conn)
        self.assertEqual(criadas, [])
        self.assertFalse(any(c.lower().lstrip().startswith('create table') for c in conn.ddl()))

    def test_update_refuses_database_that_is_not_poupe(self):
        for conn in (ConexaoFalsa(existe=False), ConexaoFalsa(existe=True),
                     ConexaoFalsa(existe=True, tabelas=['clientes', 'pedidos'])):
            with self.assertRaises(setup_db.ErroInstalacao):
                self.atualizar(conn, nome='loja')
            self.assertEqual(conn.ddl(), [])

    def test_cli_rejects_combined_options(self):
        for argv in (['--reset', '--atualizar'], ['--atualizar', '--atualizar-procedures']):
            with self.assertRaises(SystemExit), redirect_stderr(io.StringIO()):
                setup_db.main(argv)


if __name__ == '__main__':
    unittest.main()
