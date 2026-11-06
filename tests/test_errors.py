"""Erros sanitizados, cabeçalhos HTTP e inicialização sem depurador público."""
import os
from pathlib import Path
import runpy
import types
import unittest
from unittest.mock import Mock, patch

from flask import abort
from sqlalchemy.exc import StatementError
from werkzeug.exceptions import ServiceUnavailable, TooManyRequests
from backend import create_app
from backend.config import Config

ROOT = Path(__file__).resolve().parents[1]
PRIVADO = 'segredo-nao-publicar mysql://user:senha@host/banco SELECT usuario'


class ErrorTest(unittest.TestCase):
    def setUp(self):
        with patch.object(Config, 'SQLALCHEMY_DATABASE_URI', 'sqlite://'):
            self.app = create_app()
        self.client = self.app.test_client()

    def test_unexpected_error_is_safe_in_response_and_log_even_in_debug(self):
        @self.app.post('/__teste/erro')
        def falhar():
            raise StatementError(PRIVADO, 'SELECT senha FROM usuario', {'senha': PRIVADO}, ValueError(PRIVADO))

        for debug in (False, True):
            self.app.debug = debug
            with self.assertLogs(self.app.logger, level='ERROR') as logs:
                response = self.client.post('/__teste/erro', json={'senha': PRIVADO})
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json['erro'], 'Erro interno no servidor. Tente novamente mais tarde.')
            self.assertRegex(response.json['referencia'], r'^[a-f0-9]{32}$')
            self.assertEqual(response.headers['Cache-Control'], 'no-store')
            diagnostic = '\n'.join(logs.output)
            self.assertIn(response.json['referencia'], diagnostic)
            self.assertIn('StatementError', diagnostic)
            self.assertNotIn(PRIVADO, diagnostic + response.get_data(as_text=True))
            self.assertNotIn('SELECT senha', diagnostic)
            self.assertIsNone(logs.records[0].exc_info)

    def test_http_server_error_hides_description_preserves_status_and_retry(self):
        @self.app.get('/__teste/indisponivel')
        def indisponivel():
            raise ServiceUnavailable(description=PRIVADO, retry_after=17)

        with self.assertLogs(self.app.logger, level='ERROR'):
            response = self.client.get('/__teste/indisponivel')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers['Retry-After'], '17')
        self.assertNotIn(PRIVADO, response.get_data(as_text=True))

    def test_client_errors_still_preserve_messages_status_and_headers(self):
        @self.app.get('/__teste/status/<int:code>')
        def status(code):
            abort(code, description='Mensagem segura para o usuário.')

        @self.app.get('/__teste/limite')
        def limite():
            raise TooManyRequests(description='Aguarde.', retry_after=60)

        @self.app.post('/__teste/somente-post')
        def somente_post():
            return '', 204

        for code in (400, 401, 403, 404):
            response = self.client.get(f'/__teste/status/{code}')
            self.assertEqual(response.status_code, code)
            self.assertEqual(response.json['erro'], 'Mensagem segura para o usuário.')
        response = self.client.get('/__teste/limite')
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers['Retry-After'], '60')
        response = self.client.put('/__teste/somente-post')
        self.assertEqual(response.status_code, 405)
        self.assertIn('POST', response.headers['Allow'])
        self.assertTrue(response.is_json)

    def test_cors_is_not_reenabled(self):
        for method in ('GET', 'OPTIONS'):
            response = self.client.open('/usuarios/1', method=method, headers={
                'Origin': 'https://outro.example',
                'Access-Control-Request-Method': 'PUT',
                'Access-Control-Request-Headers': 'X-Poupe-Request',
            })
            self.assertNotIn('Access-Control-Allow-Origin', response.headers)
            self.assertNotIn('Access-Control-Allow-Credentials', response.headers)

    def test_debug_requires_explicit_configuration(self):
        for env, expected in (({}, False), ({'FLASK_DEBUG': '1'}, False),
                              ({'POUPE_DEBUG': 'false'}, False), ({'POUPE_DEBUG': 'true'}, True)):
            with patch.dict(os.environ, env, clear=True), patch('dotenv.load_dotenv'):
                config = runpy.run_path(str(ROOT / 'backend/config.py'))['Config']
            self.assertEqual(config.DEBUG, expected)

    def test_launcher_never_exposes_debugger_or_reloader(self):
        # Substitui totalmente o instalador do banco: jamais executa seu código.
        setup = types.ModuleType('setup_db')
        setup.ErroInstalacao = type('ErroInstalacao', (RuntimeError,), {})
        setup.criar_banco = Mock(return_value=False)
        for debug in (False, True):
            app = Mock(config={'DEBUG': debug})
            with patch.dict('sys.modules', {'setup_db': setup}), patch('backend.create_app', return_value=app):
                with self.assertRaises(SystemExit) as saida:
                    runpy.run_path(str(ROOT / 'run.py'), run_name='__main__')
            self.assertEqual(saida.exception.code, 0)
            app.run.assert_called_once_with(host='127.0.0.1', port=5000, debug=debug,
                                            use_debugger=False, use_reloader=False)

    def test_importing_launcher_never_touches_database(self):
        setup = types.ModuleType('setup_db')
        setup.ErroInstalacao = type('ErroInstalacao', (RuntimeError,), {})
        setup.criar_banco = Mock(return_value=True)
        app = Mock(config={'DEBUG': False})
        with patch.dict('sys.modules', {'setup_db': setup}), patch('backend.create_app', return_value=app):
            runpy.run_path(str(ROOT / 'run.py'), run_name='run')
        setup.criar_banco.assert_not_called()
        app.run.assert_not_called()

    def test_launcher_does_not_start_when_installer_refuses(self):
        setup = types.ModuleType('setup_db')
        setup.ErroInstalacao = type('ErroInstalacao', (RuntimeError,), {})
        setup.criar_banco = Mock(side_effect=setup.ErroInstalacao('banco parcial'))
        app = Mock(config={'DEBUG': False})
        with patch.dict('sys.modules', {'setup_db': setup}), patch('backend.create_app', return_value=app), \
                patch('sys.stderr'):
            with self.assertRaises(SystemExit) as saida:
                runpy.run_path(str(ROOT / 'run.py'), run_name='__main__')
        self.assertEqual(saida.exception.code, 1)
        app.run.assert_not_called()
