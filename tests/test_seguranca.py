"""REV-001 (limite de tentativas), REV-002 (sessão revogável e senha atual)
e REV-003 (scripts locais e cabeçalhos de segurança). SQLite em memória."""
import glob
import os
import re
import unittest
from datetime import datetime, timedelta

import test_auth
from test_auth import H
from backend.extensions import db
from backend.models.seguranca import SessaoUsuario, TentativaAcesso
from backend.models.usuario import Usuario
from backend.passwords import conferir_senha

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOVO = dict(nome="N", senha="segredo1", renda_mensal=100, limite_gastos=50)


class Base(unittest.TestCase):
    setUp = test_auth.AuthTest.setUp
    tearDown = test_auth.AuthTest.tearDown
    login = test_auth.AuthTest.login

    def entrar(self, senha="teste", email="1@teste.local", ip="10.0.0.1", client=None):
        return (client or self.client).post(
            "/login", json={"email": email, "senha": senha}, headers=H,
            environ_base={"REMOTE_ADDR": ip})


class LimiteTentativasTest(Base):  # REV-001
    def test_sexta_falha_por_email_bloqueia_ate_a_senha_certa(self):
        for _ in range(5):
            self.assertEqual(self.entrar("errada").status_code, 401)
        r = self.entrar("errada")
        self.assertEqual(r.status_code, 429)
        self.assertGreater(int(r.headers["Retry-After"]), 0)
        self.assertEqual(r.json["erro"][:16], "Muitas tentativa")
        # Bloqueado mesmo com a senha certa (senão a força bruta continuaria).
        self.assertEqual(self.entrar("teste").status_code, 429)
        # Outro e-mail, mesmo IP: segue liberado.
        self.assertEqual(self.entrar("teste", email="2@teste.local").status_code, 200)

    def test_bloqueio_expira_com_a_janela(self):
        for _ in range(5):
            self.entrar("errada")
        TentativaAcesso.query.update({"momento": datetime.now() - timedelta(minutes=16)})
        db.session.commit()
        self.assertEqual(self.entrar("teste").status_code, 200)

    def test_sucesso_zera_o_contador_do_email(self):
        for _ in range(4):
            self.entrar("errada")
        self.assertEqual(self.entrar("teste").status_code, 200)
        for _ in range(4):
            self.assertEqual(self.entrar("errada").status_code, 401)

    def test_email_nao_diferencia_maiusculas(self):
        for i in range(5):
            self.entrar("errada", email="1@TESTE.local" if i % 2 else "1@teste.local")
        self.assertEqual(self.entrar("teste").status_code, 429)

    def test_limite_por_ip_cobre_varios_emails(self):
        self.app.config["LOGIN_FALHAS_IP"] = 3
        for i in range(3):
            self.entrar("x", email=f"nao{i}@teste.local")
        self.assertEqual(self.entrar("teste").status_code, 429)
        self.assertEqual(self.entrar("teste", ip="10.0.0.2").status_code, 200)

    def test_cadastros_por_ip(self):
        self.app.config["CADASTROS_IP_HORA"] = 2
        for i in range(2):
            r = self.client.post("/usuarios", json={**NOVO, "email": f"c{i}@teste.local"}, headers=H)
            self.assertEqual(r.status_code, 201)
        # Cadastros inválidos não contam e não gastam a cota...
        self.app.config["CADASTROS_IP_HORA"] = 3
        for _ in range(5):
            self.assertEqual(self.client.post("/usuarios", json={}, headers=H).status_code, 400)
        self.assertEqual(self.client.post("/usuarios", json={**NOVO, "email": "c2@teste.local"},
                                          headers=H).status_code, 201)
        # ...mas passado o limite, nem são avaliados.
        r = self.client.post("/usuarios", json={**NOVO, "email": "c3@teste.local"}, headers=H)
        self.assertEqual(r.status_code, 429)
        self.assertIn("Retry-After", r.headers)


class SessaoTest(Base):  # REV-002
    def copiar_cookie(self):
        """Simula alguém que copiou o cookie da vítima para outro navegador."""
        outro = self.app.test_client()
        cookie = self.client.get_cookie("session")
        outro.set_cookie("session", cookie.value)
        return outro

    def test_cookie_copiado_morre_no_logout(self):
        self.login()
        ladrao = self.copiar_cookie()
        self.assertEqual(ladrao.get("/usuarios/1").status_code, 200)
        self.assertEqual(self.client.post("/logout", headers=H).status_code, 204)
        self.assertEqual(ladrao.get("/usuarios/1").status_code, 401)
        self.assertEqual(ladrao.put("/usuarios/1", json={"senha": "x"}, headers=H).status_code, 401)
        self.assertEqual(SessaoUsuario.query.count(), 0)

    def test_cookie_sem_token_ou_antigo_nao_vale(self):
        # Cookie no formato antigo (só usuario_id), assinado com a chave certa.
        with self.client.session_transaction() as s:
            s["usuario_id"] = 1
        self.assertEqual(self.client.get("/usuarios/1").status_code, 401)
        self.login()
        with self.client.session_transaction() as s:
            s["token"] = "inventado"
        self.assertEqual(self.client.get("/usuarios/1").status_code, 401)

    def test_sessao_expirada(self):
        self.login()
        SessaoUsuario.query.update({"expira_em": datetime.now() - timedelta(seconds=1)})
        db.session.commit()
        self.assertEqual(self.client.get("/usuarios/1").status_code, 401)

    def test_token_de_outro_usuario_nao_vale(self):
        self.login()
        with self.client.session_transaction() as s:
            s["usuario_id"] = 2
        self.assertEqual(self.client.get("/usuarios/2").status_code, 401)

    def test_banco_guarda_so_o_hash(self):
        self.login()
        with self.client.session_transaction() as s:
            token = s["token"]
        self.assertNotIn(token, [x.token_hash for x in SessaoUsuario.query.all()])
        self.assertEqual(len(SessaoUsuario.query.one().token_hash), 64)

    def test_troca_de_senha_exige_senha_atual(self):
        self.login()
        for extra in ({}, {"senha_atual": ""}, {"senha_atual": None}):
            r = self.client.put("/usuarios/1", json={"senha": "nova", **extra}, headers=H)
            self.assertEqual(r.status_code, 400)
        r = self.client.put("/usuarios/1", json={"senha": "nova", "senha_atual": "errada"}, headers=H)
        self.assertEqual((r.status_code, r.json["erro"]), (403, "Senha atual incorreta."))
        self.assertTrue(conferir_senha(db.session.get(Usuario, 1).senha, "teste"))
        r = self.client.put("/usuarios/1", json={"senha": "nova", "senha_atual": "teste"}, headers=H)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(conferir_senha(db.session.get(Usuario, 1).senha, "nova"))

    def test_troca_de_email_exige_senha_atual(self):
        self.login()
        r = self.client.put("/usuarios/1", json={"email": "ladrao@teste.local"}, headers=H)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(db.session.get(Usuario, 1).email, "1@teste.local")
        # Reenviar o mesmo e-mail (tela de perfil) não pede senha.
        r = self.client.put("/usuarios/1", json={"email": "1@teste.local", "nome": "Ana"}, headers=H)
        self.assertEqual(r.status_code, 200)
        r = self.client.put("/usuarios/1", json={"email": "novo@teste.local", "senha_atual": "teste"},
                            headers=H)
        self.assertEqual((r.status_code, r.json["email"]), (200, "novo@teste.local"))

    def test_troca_de_senha_derruba_outros_aparelhos_e_mantem_este(self):
        self.login()
        outro = self.app.test_client()
        self.assertEqual(self.entrar(client=outro).status_code, 200)
        ladrao = self.copiar_cookie()
        r = self.client.put("/usuarios/1", json={"senha": "nova", "senha_atual": "teste"}, headers=H)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.get("/usuarios/1").status_code, 200)
        self.assertEqual(outro.get("/usuarios/1").status_code, 401)
        # O cookie copiado é o mesmo deste aparelho: segue válido até o logout,
        # mas a senha nova não é conhecida pelo atacante.
        self.assertEqual(ladrao.get("/usuarios/1").status_code, 200)

    def test_senha_atual_errada_conta_como_tentativa(self):
        self.login()
        for _ in range(5):
            self.client.put("/usuarios/1", json={"senha": "n", "senha_atual": "x"}, headers=H)
        r = self.client.put("/usuarios/1", json={"senha": "n", "senha_atual": "teste"}, headers=H)
        self.assertEqual(r.status_code, 429)
        self.assertEqual(self.entrar("teste").status_code, 429)


class CabecalhosTest(Base):  # REV-003
    def test_cabecalhos_em_paginas_e_api(self):
        for url in ("/", "/inicio.html", "/categorias", "/nao-existe.js"):
            r = self.client.get(url)
            with self.subTest(url=url):
                csp = r.headers.get("Content-Security-Policy", "")
                self.assertIn("script-src 'self'", csp)
                self.assertIn("frame-ancestors 'none'", csp)
                self.assertIn("object-src 'none'", csp)
                self.assertNotRegex(csp, r"https?:")
                self.assertEqual(r.headers.get("X-Content-Type-Options"), "nosniff")
                self.assertEqual(r.headers.get("X-Frame-Options"), "DENY")
                self.assertEqual(r.headers.get("Referrer-Policy"), "same-origin")

    def test_paginas_sem_scripts_externos(self):
        paginas = glob.glob(os.path.join(RAIZ, "frontend", "*.html"))
        self.assertGreater(len(paginas), 10)
        for caminho in paginas:
            html = open(caminho, encoding="utf-8").read()
            with self.subTest(pagina=os.path.basename(caminho)):
                for src in re.findall(r"<script[^>]*\bsrc=\"([^\"]+)\"", html):
                    self.assertFalse(re.match(r"(https?:)?//", src), src)
                    self.assertTrue(os.path.isfile(os.path.join(RAIZ, "frontend", src)), src)

    def test_bibliotecas_locais_sao_servidas(self):
        for nome in ("lucide-1.69.0.min.js", "chart-4.6.1.umd.min.js"):
            r = self.client.get(f"/vendor/{nome}")
            self.assertEqual(r.status_code, 200)
            self.assertIn("javascript", r.mimetype)
            r.close()


if __name__ == "__main__":
    unittest.main()
