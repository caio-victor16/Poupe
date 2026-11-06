"""Item 12: validação de gastos, boletos, período e cadastro/perfil de usuário.

SQLite em memória; não acessa o MySQL.
"""
import unittest

from backend.config import Config
Config.SQLALCHEMY_DATABASE_URI = "sqlite://"
from backend import create_app
from backend.extensions import db
from backend.models.boleto import Boleto
from backend.models.categoria import Categoria
from backend.models.gasto import Gasto
from backend.models.usuario import Usuario

H = {"X-Poupe-Request": "1"}
GASTO = {"id_categoria": 1, "valor": "49.90", "data": "2026-11-05", "descricao": "Mercado"}
CODIGO = "23793.38128 60000.000003 00000.000400 1 84340000010000"   # 47 dígitos
BOLETO = {"codigo_barras": CODIGO, "valor": 100, "vencimento": "2026-11-20"}
USUARIO = {"nome": "Ana", "email": "ana@teste.com", "senha": "segredo1",
           "renda_mensal": 3000, "limite_gastos": 1500}


class Base(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        db.session.add(Usuario(id_usuario=1, nome="1", email="1@teste.local", senha="teste",
                               renda_mensal=1000, limite_gastos=500))
        db.session.add(Categoria(id_categoria=1, nome="alimentação"))
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def login(self):
        r = self.client.post("/login", json={"email": "1@teste.local", "senha": "teste"}, headers=H)
        self.assertEqual(r.status_code, 200)

    def todos_400(self, metodo, url, base, casos):
        for extra in casos:
            with self.subTest(url=url, extra=extra):
                r = self.client.open(url, method=metodo, json={**base, **extra}, headers=H)
                self.assertEqual(r.status_code, 400, r.get_data(as_text=True))
                self.assertIn("erro", r.json)


class GastoTest(Base):
    def setUp(self):
        super().setUp()
        self.login()

    def test_criacao_valida_e_normaliza(self):
        r = self.client.post("/gastos", json={**GASTO, "descricao": "  ", "valor": "10.005"}, headers=H)
        self.assertEqual(r.status_code, 201)
        self.assertEqual((r.json["valor"], r.json["descricao"], r.json["recorrente"]), (10.01, None, False))

    def test_criacao_invalida(self):
        self.todos_400("POST", "/gastos", GASTO, [
            {"valor": 0}, {"valor": -1}, {"valor": "abc"}, {"valor": "NaN"}, {"valor": True},
            {"valor": "100000000"}, {"id_categoria": 999}, {"id_categoria": "x"}, {"id_categoria": 0},
            {"data": "05/11/2026"}, {"data": "2026-02-30"}, {"data": "0026-11-05"},
            {"descricao": "x" * 256}, {"descricao": 5}, {"recorrente": "sim"},
        ])
        for falta in ("id_categoria", "valor", "data"):
            dados = {k: v for k, v in GASTO.items() if k != falta}
            self.assertEqual(self.client.post("/gastos", json=dados, headers=H).status_code, 400, falta)
        self.assertEqual(Gasto.query.count(), 0)

    def test_atualizacao_valida_tudo_antes_de_alterar(self):
        gid = self.client.post("/gastos", json=GASTO, headers=H).json["id_gasto"]
        # Antes: PUT gravava qualquer valor e um ValueError virava 500.
        self.todos_400("PUT", f"/gastos/{gid}", {}, [
            {"valor": "abc"}, {"valor": -5}, {"data": "ontem"}, {"id_categoria": 42},
            {"descricao": "Novo", "valor": 0},
        ])
        gasto = db.session.get(Gasto, gid)
        self.assertEqual((float(gasto.valor), gasto.descricao), (49.9, "Mercado"))
        r = self.client.put(f"/gastos/{gid}", json={"valor": 60, "descricao": ""}, headers=H)
        self.assertEqual((r.status_code, r.json["valor"], r.json["descricao"]), (200, 60.0, None))

    def test_periodo_valida_datas(self):
        base = "/gastos/usuario/1/periodo"
        for qs in ("inicio=ontem&fim=2026-11-30", "inicio=2026-11-30&fim=2026-11-01",
                   "inicio=2026-13-01&fim=2026-12-01"):
            self.assertEqual(self.client.get(f"{base}?{qs}").status_code, 400, qs)


class BoletoTest(Base):
    def setUp(self):
        super().setUp()
        self.login()

    def test_boleto_valido_grava_so_digitos(self):
        r = self.client.post("/boletos", json=BOLETO, headers=H)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json["codigo_barras"], "".join(ch for ch in CODIGO if ch.isdigit()))
        self.assertEqual(r.json["status"], "pendente")

    def test_boleto_invalido(self):
        self.todos_400("POST", "/boletos", BOLETO, [
            {"codigo_barras": "123"}, {"codigo_barras": "abc" * 20}, {"codigo_barras": "9" * 49},
            {"codigo_barras": ""}, {"codigo_barras": 123}, {"valor": 0}, {"valor": "x"},
            {"vencimento": "amanhã"}, {"status": "talvez"},
        ])
        self.assertEqual(Boleto.query.count(), 0)
        bid = self.client.post("/boletos", json=BOLETO, headers=H).json["id_boleto"]
        self.todos_400("PUT", f"/boletos/{bid}", {}, [{"valor": -1}, {"status": "x"}, {"vencimento": "2026-02-31"}])
        r = self.client.put(f"/boletos/{bid}", json={"status": "pago"}, headers=H)
        self.assertEqual((r.status_code, r.json["status"]), (200, "pago"))


class UsuarioTest(Base):
    def test_renda_zero_e_aceita(self):
        # Antes: renda 0 era recusada como "campo obrigatório".
        r = self.client.post("/usuarios", json={**USUARIO, "renda_mensal": 0}, headers=H)
        self.assertEqual(r.status_code, 201, r.json)
        self.assertEqual(float(db.session.get(Usuario, r.json["usuario_id"]).renda_mensal), 0.0)

    def test_cadastro_invalido(self):
        self.todos_400("POST", "/usuarios", USUARIO, [
            {"limite_gastos": 0}, {"limite_gastos": -1}, {"renda_mensal": -1}, {"renda_mensal": "abc"},
            {"email": "sem-arroba"}, {"email": "a@b"}, {"email": ""}, {"nome": " "},
            {"nome": "x" * 101}, {"telefone": "abc"}, {"senha": ""},
        ])
        sem_senha = {k: v for k, v in USUARIO.items() if k != "senha"}
        self.assertEqual(self.client.post("/usuarios", json=sem_senha, headers=H).status_code, 400)
        self.assertEqual(Usuario.query.count(), 1)

    def test_mensagem_de_limite_zero_e_clara(self):
        r = self.client.post("/usuarios", json={**USUARIO, "limite_gastos": 0}, headers=H)
        self.assertIn("maior que", r.json["erro"])
        self.assertNotIn("obrigatório", r.json["erro"])

    def test_perfil_valida_antes_de_alterar(self):
        self.login()
        self.todos_400("PUT", "/usuarios/1", {}, [
            {"email": "invalido"}, {"limite_gastos": 0}, {"nome": "Novo", "renda_mensal": -1},
            {"telefone": "x" * 30},
        ])
        usuario = db.session.get(Usuario, 1)
        self.assertEqual((usuario.nome, usuario.email), ("1", "1@teste.local"))
        r = self.client.put("/usuarios/1", json={"nome": " Bia ", "telefone": "(11) 98888-7777", "renda_mensal": 0},
                            headers=H)
        self.assertEqual(r.status_code, 200, r.json)
        self.assertEqual((r.json["nome"], r.json["telefone"], r.json["renda_mensal"]), ("Bia", "(11) 98888-7777", 0.0))
        r = self.client.put("/usuarios/1", json={"telefone": ""}, headers=H)
        self.assertIsNone(r.json["telefone"])


if __name__ == "__main__":
    unittest.main()
