import unittest
import test_auth
from test_auth import H
from backend.extensions import db
from backend.models.usuario import Usuario
from backend.passwords import gerar_hash, conferir_senha
from migrar_senhas import migrar


class PasswordTest(unittest.TestCase):
    setUp = test_auth.AuthTest.setUp
    tearDown = test_auth.AuthTest.tearDown
    login = test_auth.AuthTest.login
    def test_signup_and_salt(self):
        for email in ('a@teste.local', 'b@teste.local'):
            r = self.client.post('/usuarios', headers=H, json=dict(
                nome='Teste', email=email, senha='Senha ç segura', renda_mensal=100, limite_gastos=50))
            self.assertEqual(r.status_code, 201)
        a = Usuario.buscar_por_email('a@teste.local')
        b = Usuario.buscar_por_email('b@teste.local')
        self.assertNotEqual(a.senha, 'Senha ç segura')
        self.assertNotEqual(a.senha, b.senha)
        self.assertLessEqual(len(a.senha), 255)
        self.assertTrue(conferir_senha(a.senha, 'Senha ç segura'))
        self.assertFalse(conferir_senha(a.senha, a.senha))
        self.assertNotIn('senha', a.to_dict())

    def test_legacy_login_migrates_only_correct_password(self):
        r = self.client.post('/login', headers=H, json={'email': '1@teste.local', 'senha': 'errada'})
        self.assertEqual(r.status_code, 401)
        self.assertEqual(db.session.get(Usuario, 1).senha, 'teste')
        self.login()
        hashed = db.session.get(Usuario, 1).senha
        self.assertTrue(hashed.startswith('scrypt:'))
        self.login()
        self.assertEqual(db.session.get(Usuario, 1).senha, hashed)

    def test_password_change_and_validation(self):
        self.login()
        for bad in ('', None, [], 123, 'a' * 1025):
            self.assertEqual(self.client.put('/usuarios/1', headers=H, json={'senha': bad}).status_code, 400)
        self.assertEqual(self.client.put('/usuarios/1', headers=H, json={'senha': 'nova', 'senha_atual': 'teste'}).status_code, 200)
        stored = db.session.get(Usuario, 1).senha
        self.assertTrue(conferir_senha(stored, 'nova'))
        self.assertFalse(conferir_senha(stored, 'teste'))
        self.client.put('/usuarios/1', headers=H, json={'nome': 'Novo nome'})
        self.assertEqual(db.session.get(Usuario, 1).senha, stored)
        self.assertEqual(self.client.post('/login', headers=H, json={'email': '1@teste.local', 'senha': []}).status_code, 400)

    def test_batch_migration_is_idempotent(self):
        self.assertEqual(migrar(), 2)
        stored = db.session.get(Usuario, 1).senha
        self.assertEqual(migrar(), 0)
        self.assertEqual(db.session.get(Usuario, 1).senha, stored)
        self.login()

    def test_corrupt_hash_never_falls_back_to_plaintext(self):
        self.assertFalse(conferir_senha('scrypt:broken', 'scrypt:broken'))
