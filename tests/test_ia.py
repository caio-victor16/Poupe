import unittest
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch, Mock
import test_auth
from test_auth import H
from backend.services.ia_limite import reservar_chamada
from backend.services.ia_service import GeminiService, ErroIA
import requests


class IATest(unittest.TestCase):
    def setUp(self):
        test_auth.AuthTest.setUp(self)
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, 'limites.sqlite3')
        self.app.config.update(IA_LIMITES_DB=self.path, IA_LIMITE_MINUTO=2)
        test_auth.AuthTest.login(self)

    def tearDown(self):
        test_auth.AuthTest.tearDown(self)
        self.tmp.cleanup()

    def test_limit_blocks_before_provider_and_survives_logout(self):
        with patch.object(GeminiService, 'gerar_resposta', return_value='ok') as provider:
            for _ in range(2):
                self.assertEqual(self.client.post('/ia', headers=H, json={'mensagem': 'Oi'}).status_code, 200)
            self.client.post('/logout', headers=H)
            test_auth.AuthTest.login(self)
            response = self.client.post('/ia', headers=H, json={'mensagem': 'Oi'})
            self.assertEqual(response.status_code, 429)
            self.assertGreater(int(response.headers['Retry-After']), 0)
            self.assertEqual(provider.call_count, 2)

    def test_invalid_messages_and_fail_closed(self):
        with patch.object(GeminiService, 'gerar_resposta') as provider:
            for value in ('   ', 'a' * 2001, 123):
                self.assertEqual(self.client.post('/ia', headers=H, json={'mensagem': value}).status_code, 400)
            with patch('backend.controllers.ia_controller.reservar_chamada', side_effect=OSError):
                self.assertEqual(self.client.post('/ia', headers=H, json={'mensagem': 'Oi'}).status_code, 503)
            provider.assert_not_called()

    def test_atomic_persistent_limits_and_reset(self):
        limits = [('min', 60, 3, False), ('global', 60, 4, True)]
        with ThreadPoolExecutor(max_workers=8) as pool:
            result = list(pool.map(lambda _: reservar_chamada(self.path, 1, limits, 120), range(8)))
        self.assertEqual(result.count(0), 3)
        self.assertEqual(reservar_chamada(self.path, 2, limits, 120), 0)
        self.assertEqual(reservar_chamada(self.path, 3, limits, 120), 60)
        self.assertEqual(reservar_chamada(self.path, 1, limits, 180), 0)

    def test_timeout_does_not_retry_or_log_private_data(self):
        service = GeminiService()
        service.api_key = 'segredo-teste'
        with patch('backend.services.ia_service.requests.post', side_effect=requests.Timeout('conteudo privado')) as post:
            with patch('builtins.print') as output:
                with self.assertRaisesRegex(RuntimeError, 'demorou'):
                    service.gerar_resposta('mensagem privada')
                post.assert_called_once()
                output.assert_not_called()

    def test_success_has_no_content_logging(self):
        service = GeminiService()
        service.api_key = 'teste'
        response = Mock(status_code=200)
        response.json.return_value = {'candidates': [{'content': {'parts': [{'text': 'resposta privada'}]}}]}
        with patch('backend.services.ia_service.requests.post', return_value=response), patch('builtins.print') as output:
            self.assertEqual(service.gerar_resposta('mensagem privada'), 'resposta privada')
            output.assert_not_called()

    def test_unexpected_runtime_error_is_not_treated_as_public_message(self):
        with patch.object(GeminiService, 'gerar_resposta', side_effect=RuntimeError('senha-secreta')):
            with self.assertLogs(self.app.logger, level='WARNING') as logs:
                response = self.client.post('/ia', headers=H, json={'mensagem': 'Oi'})
        self.assertEqual(response.status_code, 500)
        self.assertNotIn('senha-secreta', response.get_data(as_text=True) + '\n'.join(logs.output))
        with patch.object(GeminiService, 'gerar_resposta', side_effect=ErroIA('Mensagem pública.')):
            response = self.client.post('/ia', headers=H, json={'mensagem': 'Oi'})
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json['erro'], 'Mensagem pública.')
