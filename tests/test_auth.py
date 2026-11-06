"""Testes isolados: não importam run.py nem acessam o MySQL."""
import unittest
from datetime import date
from backend.config import Config
Config.SQLALCHEMY_DATABASE_URI = "sqlite://"
from backend import create_app
from backend.extensions import db
from backend.models.usuario import Usuario
from backend.models.categoria import Categoria
from backend.auth import RECURSOS

H = {"X-Poupe-Request": "1"}


class AuthTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        for uid in (1, 2):
            db.session.add(Usuario(id_usuario=uid, nome=str(uid), email=f"{uid}@teste.local",
                                   senha="teste", renda_mensal=1000, limite_gastos=500))
        db.session.add(Categoria(id_categoria=1, nome="Teste"))
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def login(self):
        r = self.client.post("/login", json={"email": "1@teste.local", "senha": "teste"}, headers=H)
        self.assertEqual(r.status_code, 200)
        return r

    def test_login_logout_and_cookie(self):
        self.assertEqual(self.client.get('/usuarios/1').status_code, 401)
        cookie = self.login().headers['Set-Cookie']
        self.assertIn('HttpOnly', cookie)
        self.assertIn('SameSite=Strict', cookie)
        self.assertEqual(self.client.get('/usuarios/1').status_code, 200)
        self.assertEqual(self.client.post('/logout', headers=H).status_code, 204)
        self.assertEqual(self.client.get('/usuarios/1').status_code, 401)

    def test_all_api_routes_require_login(self):
        import re
        for rule in self.app.url_map.iter_rules():
            if '.' not in rule.endpoint or rule.endpoint in {'usuario.login', 'usuario.cadastrar_usuario'}:
                continue
            url = re.sub(r'<int:[^>]+>', '1', rule.rule)
            for method in rule.methods - {'HEAD', 'OPTIONS'}:
                with self.subTest(url=url, method=method):
                    self.assertEqual(self.client.open(url, method=method, headers=H).status_code, 401)

    def test_cross_user_and_global_access(self):
        self.login()
        for method in ('GET', 'PUT', 'DELETE'):
            self.assertEqual(self.client.open('/usuarios/2', method=method, headers=H, json={}).status_code, 403)
        for path in ('/usuarios', '/gastos', '/boletos', '/gastos/usuario/2', '/score/usuario/2'):
            self.assertEqual(self.client.get(path).status_code, 403)
        self.assertEqual(self.client.post('/categorias', json={'nome': 'X'}, headers=H).status_code, 403)
        self.assertEqual(self.client.get('/categorias').status_code, 200)

    def test_resource_ownership(self):
        self.login()
        paths = {'gasto': '/gastos', 'boleto': '/boletos', 'alerta': '/alertas',
                 'orcamento': '/orcamentos', 'recorrencia_gasto': '/recorrencias',
                 'receita': '/receitas', 'conta': '/contas', 'meta': '/metas',
                 'cofrinho_meta': '/cofrinhos', 'receita_recorrente': '/receitas-recorrentes'}
        values = dict(id_categoria=1, valor=10, data=date.today(), vencimento=date.today(),
                      codigo_barras='123', limite=100, frequencia='mensal',
                      proxima_data=date.today(), dia_mes=1, descricao='x', categoria='Outros',
                      nome='x', tipo='Corrente', saldo=1, titulo='x', valor_alvo=10,
                      valor_guardado=0, prazo_meses=1, ativa=True)
        for name, (pk, model) in RECURSOS.items():
            row = model(id_usuario=2, **{k: v for k, v in values.items() if hasattr(model, k)})
            db.session.add(row)
            db.session.commit()
            path = f'{paths[name]}/{getattr(row, pk)}'
            self.assertEqual(self.client.delete(path, headers=H).status_code, 404)
            self.assertIsNotNone(db.session.get(model, getattr(row, pk)))

    def test_creation_identity_and_csrf(self):
        self.assertEqual(self.client.post('/login', json={}).status_code, 403)
        self.login()
        self.assertEqual(self.client.post('/alertas', json={'id_usuario': 2}, headers=H).status_code, 403)
        r = self.client.post('/alertas', json={'tipo': 'teste', 'mensagem': 'teste'}, headers=H)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json['id_usuario'], 1)
        self.assertEqual(self.client.post('/logout').status_code, 403)
        r = self.client.options('/logout', headers={'Origin': 'https://outro.example', 'Access-Control-Request-Method': 'POST'})
        self.assertNotIn('Access-Control-Allow-Origin', r.headers)


if __name__ == '__main__':
    unittest.main()
