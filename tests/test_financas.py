"""Contas, metas, cofrinhos e receitas fixas (item 10c, parte 2).

SQLite em memória; não acessa o MySQL.
"""
import unittest
from datetime import date

from backend.config import Config
Config.SQLALCHEMY_DATABASE_URI = "sqlite://"
from backend import create_app
from backend.controllers.financas_controller import _primeira_data, processar_receitas
from backend.extensions import db
from backend.models.cofrinho import Cofrinho
from backend.models.receita import Receita
from backend.models.receita_recorrente import ReceitaRecorrente
from backend.models.usuario import Usuario

H = {"X-Poupe-Request": "1"}


class FinancasTest(unittest.TestCase):
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
        self.assertEqual(self.client.post("/login", json={"email": "1@teste.local", "senha": "teste"},
                                          headers=H).status_code, 200)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def post(self, url, **dados):
        return self.client.post(url, json=dados, headers=H)

    def invalidos(self, url, base, casos):
        for extra in casos:
            with self.subTest(url=url, extra=extra):
                r = self.post(url, **{**base, **extra})
                self.assertEqual(r.status_code, 400, r.json)

    # --- contas -------------------------------------------------------------------

    def test_contas(self):
        r = self.post("/contas", nome="Nubank", tipo="Corrente", saldo="1500.75")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json["id_usuario"], 1)
        self.assertEqual(self.post("/contas", nome="Cheque especial", tipo="Corrente", saldo=-200).status_code, 201)
        lista = self.client.get("/contas/usuario/1").json
        self.assertEqual([c["saldo"] for c in lista], [1500.75, -200.0])     # negativo permitido
        r = self.client.put(f"/contas/{lista[0]['id_conta']}", json={"saldo": 99}, headers=H)
        self.assertEqual((r.status_code, r.json["saldo"], r.json["nome"]), (200, 99.0, "Nubank"))
        self.invalidos("/contas", {"nome": "X", "tipo": "Corrente", "saldo": 1}, [
            {"tipo": "Cripto"}, {"nome": ""}, {"nome": "x" * 101}, {"saldo": "abc"},
            {"saldo": "NaN"}, {"saldo": True}, {"saldo": None}, {"saldo": "100000000"}])
        self.assertEqual(self.client.delete(f"/contas/{lista[1]['id_conta']}", headers=H).status_code, 204)
        self.assertEqual(len(self.client.get("/contas/usuario/1").json), 1)

    # --- metas --------------------------------------------------------------------

    def test_metas(self):
        r = self.post("/metas", titulo="Viagem", valor_alvo=5000, valor_guardado="1200.5")
        self.assertEqual((r.status_code, r.json["valor_guardado"]), (201, 1200.5))
        self.invalidos("/metas", {"titulo": "X", "valor_alvo": 10, "valor_guardado": 0}, [
            {"valor_alvo": 0}, {"valor_alvo": -1}, {"valor_guardado": -1}, {"titulo": "  "}])
        self.assertEqual(self.post("/metas", titulo="Sem guardado", valor_alvo=10).status_code, 400)
        r = self.client.put(f"/metas/{r.json['id_meta']}", json={"valor_alvo": 0}, headers=H)
        self.assertEqual(r.status_code, 400)

    # --- cofrinhos ----------------------------------------------------------------

    def test_cofrinhos_e_aporte(self):
        r = self.post("/cofrinhos", titulo="Reserva", valor_alvo=1000, valor_guardado=0, prazo_meses=10)
        self.assertEqual(r.status_code, 201)
        cid = r.json["id_cofrinho"]
        self.invalidos("/cofrinhos", {"titulo": "X", "valor_alvo": 10, "valor_guardado": 0, "prazo_meses": 1}, [
            {"prazo_meses": 0}, {"prazo_meses": 601}, {"prazo_meses": "x"}, {"prazo_meses": True},
            {"prazo_meses": 2.5}])
        for valor in ("100.10", 50):
            self.assertEqual(self.post(f"/cofrinhos/{cid}/aportar", valor=valor).status_code, 200)
        self.assertEqual(self.client.get("/cofrinhos/usuario/1").json[0]["valor_guardado"], 150.10)
        for valor in (0, -5, "abc", None):
            self.assertEqual(self.post(f"/cofrinhos/{cid}/aportar", valor=valor).status_code, 400)
        self.assertEqual(self.post("/cofrinhos/999/aportar", valor=1).status_code, 404)

    # --- receitas fixas ----------------------------------------------------------

    def test_primeira_data(self):
        hoje = date(2026, 11, 10)
        self.assertEqual(_primeira_data(15, hoje), date(2026, 11, 15))
        self.assertEqual(_primeira_data(10, hoje), date(2026, 11, 10))
        self.assertEqual(_primeira_data(5, hoje), date(2026, 12, 5))
        self.assertEqual(_primeira_data(31, hoje), date(2026, 11, 30))
        self.assertEqual(_primeira_data(5, date(2026, 12, 20)), date(2027, 1, 5))

    def test_receita_fixa_gera_receitas_sem_duplicar(self):
        r = self.post("/receitas-recorrentes", descricao="Salário", categoria="Salário", valor=5000, dia_mes=31)
        self.assertEqual(r.status_code, 201)
        rec = db.session.get(ReceitaRecorrente, r.json["id_receita_recorrente"])
        rec.proxima_data = date(2026, 1, 31)        # simula atraso de vários meses
        db.session.commit()

        geradas = processar_receitas(1, hoje=date(2026, 4, 15))
        self.assertEqual([g["data"] for g in geradas], ["2026-01-31", "2026-02-28", "2026-03-31"])
        self.assertEqual(db.session.get(ReceitaRecorrente, rec.id_receita_recorrente).proxima_data, date(2026, 4, 30))
        self.assertEqual(processar_receitas(1, hoje=date(2026, 4, 15)), [])      # idempotente
        self.assertEqual(Receita.query.filter_by(id_usuario=1).count(), 3)

        self.client.put(f"/receitas-recorrentes/{rec.id_receita_recorrente}", json={"ativa": False}, headers=H)
        self.assertEqual(processar_receitas(1, hoje=date(2027, 1, 1)), [])       # inativa não gera
        self.assertEqual(self.client.put(f"/receitas-recorrentes/{rec.id_receita_recorrente}",
                                         json={"ativa": "sim"}, headers=H).status_code, 400)

    def test_receita_fixa_validacao_e_rota_de_processar(self):
        self.invalidos("/receitas-recorrentes", {"descricao": "X", "categoria": "Outros", "valor": 1, "dia_mes": 5}, [
            {"categoria": "Herança"}, {"valor": 0}, {"dia_mes": 0}, {"dia_mes": 32}, {"dia_mes": "x"}])
        r = self.client.post("/receitas-recorrentes/usuario/1/processar", headers=H)
        self.assertEqual((r.status_code, r.json["geradas"]), (200, 0))

    # --- isolamento ---------------------------------------------------------------

    def test_isolamento_entre_usuarios(self):
        alheio = Cofrinho(id_usuario=2, titulo="Do outro", valor_alvo=10, valor_guardado=1, prazo_meses=1)
        db.session.add(alheio)
        db.session.commit()
        for url in ("/contas/usuario/2", "/metas/usuario/2", "/cofrinhos/usuario/2",
                    "/receitas-recorrentes/usuario/2"):
            self.assertEqual(self.client.get(url).status_code, 403, url)
        self.assertEqual(self.client.post("/receitas-recorrentes/usuario/2/processar", headers=H).status_code, 403)
        self.assertEqual(self.post(f"/cofrinhos/{alheio.id_cofrinho}/aportar", valor=999).status_code, 404)
        self.assertEqual(self.client.put(f"/cofrinhos/{alheio.id_cofrinho}", json={"titulo": "Meu"}, headers=H).status_code, 404)
        self.assertEqual(self.client.delete(f"/cofrinhos/{alheio.id_cofrinho}", headers=H).status_code, 404)
        self.assertEqual(self.post("/contas", id_usuario=2, nome="X", tipo="Corrente", saldo=1).status_code, 403)
        db.session.refresh(alheio)
        self.assertEqual((alheio.titulo, float(alheio.valor_guardado)), ("Do outro", 1.0))


if __name__ == "__main__":
    unittest.main()
