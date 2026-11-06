"""API de receitas (item 10c): CRUD, validação e isolamento entre usuários.

Banco SQLite em memória; não acessa o MySQL.
"""
import unittest

from backend.config import Config
Config.SQLALCHEMY_DATABASE_URI = "sqlite://"
from backend import create_app
from backend.extensions import db
from backend.models.receita import Receita
from backend.models.usuario import Usuario

H = {"X-Poupe-Request": "1"}
VALIDA = {"descricao": "Salário novembro", "categoria": "Salário", "valor": "5000.50", "data": "2026-11-05"}


class ReceitaTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        for uid in (1, 2):
            db.session.add(Usuario(id_usuario=uid, nome=str(uid), email=f"{uid}@teste.local",
                                   senha="teste", renda_mensal=1000, limite_gastos=500))
        db.session.commit()
        self.client = self.app.test_client()
        r = self.client.post("/login", json={"email": "1@teste.local", "senha": "teste"}, headers=H)
        self.assertEqual(r.status_code, 200)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def criar(self, **extra):
        return self.client.post("/receitas", json={**VALIDA, **extra}, headers=H)

    def test_crud_completo(self):
        r = self.criar()
        self.assertEqual(r.status_code, 201)
        criada = r.json
        self.assertEqual(criada["id_usuario"], 1)                  # vem da sessão
        self.assertEqual(criada["valor"], 5000.5)
        self.assertEqual(criada["data"], "2026-11-05")

        self.criar(descricao="Freela", categoria="Trabalho", valor=800, data="2026-10-20")
        lista = self.client.get("/receitas/usuario/1").json
        self.assertEqual([x["descricao"] for x in lista], ["Salário novembro", "Freela"])  # mais recente primeiro

        r = self.client.put(f"/receitas/{criada['id_receita']}", json={"valor": 5100}, headers=H)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["valor"], 5100.0)
        self.assertEqual(r.json["descricao"], "Salário novembro")   # parcial preserva o resto

        self.assertEqual(self.client.delete(f"/receitas/{criada['id_receita']}", headers=H).status_code, 204)
        self.assertEqual(len(self.client.get("/receitas/usuario/1").json), 1)
        self.assertEqual(self.client.delete(f"/receitas/{criada['id_receita']}", headers=H).status_code, 404)

    def test_validacoes(self):
        invalidos = [
            {"valor": 0}, {"valor": -5}, {"valor": "abc"}, {"valor": True}, {"valor": "NaN"},
            {"valor": "Infinity"}, {"valor": "100000000"}, {"valor": None},
            {"categoria": "Herança"}, {"categoria": None},
            {"data": "05/11/2026"}, {"data": "2026-02-30"}, {"data": None},
            {"descricao": ""}, {"descricao": "   "}, {"descricao": "x" * 256}, {"descricao": 123},
        ]
        for extra in invalidos:
            with self.subTest(extra=extra):
                r = self.criar(**extra)
                self.assertEqual(r.status_code, 400)
                self.assertIn("erro", r.json)
        for faltando in VALIDA:
            with self.subTest(faltando=faltando):
                dados = {k: v for k, v in VALIDA.items() if k != faltando}
                self.assertEqual(self.client.post("/receitas", json=dados, headers=H).status_code, 400)
        self.assertEqual(self.client.post("/receitas", data="x", headers=H,
                                          content_type="application/json").status_code, 400)
        self.assertEqual(Receita.query.count(), 0)

    def test_valor_arredondado_e_descricao_aparada(self):
        r = self.criar(valor="10.005", descricao="  Bônus  ")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json["descricao"], "Bônus")
        self.assertEqual(r.json["valor"], 10.01)                   # meio centavo arredonda para cima

    def test_atualizacao_invalida_nao_altera(self):
        criada = self.criar().json
        r = self.client.put(f"/receitas/{criada['id_receita']}", json={"valor": -1, "descricao": "Novo"}, headers=H)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(db.session.get(Receita, criada["id_receita"]).descricao, "Salário novembro")

    def test_isolamento_entre_usuarios(self):
        alheia = Receita(id_usuario=2, descricao="Do outro", categoria="Outros", valor=1, data=Receita.data.type.python_type(2026, 11, 1))
        db.session.add(alheia)
        db.session.commit()
        self.assertEqual(self.client.get("/receitas/usuario/2").status_code, 403)
        self.assertEqual(self.client.put(f"/receitas/{alheia.id_receita}", json={"valor": 9}, headers=H).status_code, 404)
        self.assertEqual(self.client.delete(f"/receitas/{alheia.id_receita}", headers=H).status_code, 404)
        self.assertEqual(self.criar(id_usuario=2).status_code, 403)
        self.assertNotIn("Do outro", str(self.client.get("/receitas/usuario/1").json))
        self.assertEqual(float(db.session.get(Receita, alheia.id_receita).valor), 1.0)

    def test_exige_login_e_cabecalho(self):
        self.assertEqual(self.client.post("/receitas", json=VALIDA).status_code, 403)   # sem X-Poupe-Request
        self.client.post("/logout", headers=H)
        self.assertEqual(self.client.get("/receitas/usuario/1").status_code, 401)


if __name__ == "__main__":
    unittest.main()
