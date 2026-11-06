"""E2E do item 14 (alerta de limite sem repetição): navegador real + Flask + MySQL/MariaDB.

Cadastra gastos pela tela de gastos (que dispara a geração do alerta a cada
gasto acima de 80% do limite) e confere quantos alertas existem.
NÃO rodar contra o banco real. Mesmos pré-requisitos e variáveis de
tests/e2e/e2e_recorrencias.py (banco DESCARTÁVEL; MYSQL_DATABASE diferente de "poupe").
"""
import datetime as dt
import os
import subprocess

from playwright.sync_api import sync_playwright

BASE = os.getenv("POUPE_URL", "http://127.0.0.1:5000")
BANCO = os.getenv("MYSQL_DATABASE", "poupe_e2e")
if BANCO == "poupe":
    raise SystemExit("Use um banco descartável (MYSQL_DATABASE diferente de 'poupe').")
HOJE = dt.date.today()
EMAIL = f"ale{dt.datetime.now():%H%M%S%f}@teste.com"
erros, alertas = [], []


def sql(q):
    return subprocess.run(
        ["mysql", f"-u{os.getenv('MYSQL_USER', 'root')}", f"-h{os.getenv('MYSQL_HOST', '127.0.0.1')}", "-N", BANCO, "-e", q],
        env={**os.environ, "MYSQL_PWD": os.getenv("MYSQL_PASSWORD", "")},
        capture_output=True, text=True, check=True).stdout.strip()


def ok(cond, msg):
    print(("OK   " if cond else "FALHA ") + msg)
    if not cond:
        raise SystemExit(1)


with sync_playwright() as p:
    chrome = os.getenv("CHROME_PATH")
    nav = p.chromium.launch(executable_path=chrome, args=["--no-sandbox"]) if chrome else p.chromium.launch()
    # wait_for_function avalia texto no navegador; a CSP (REV-003) bloqueia eval.
    page = nav.new_page(bypass_csp=True)
    page.route("https://unpkg.com/**", lambda r: r.fulfill(
        content_type="application/javascript",
        body="window.lucide={createIcons(){document.querySelectorAll('[data-lucide]:empty')"
             ".forEach(e=>e.textContent='•')}};"))
    page.on("pageerror", lambda e: erros.append(f"{page.url}: {e}"))
    page.on("dialog", lambda d: (alertas.append(d.message), d.accept()))

    page.goto(f"{BASE}/cadastro.html")
    page.fill("#name", "Alerta"); page.fill("#email", EMAIL); page.fill("#password", "senha123")
    page.fill("#income", "5000"); page.fill("#limit", "1000")
    page.click("button[type=submit]"); page.wait_for_url("**/login.html")
    page.fill("#email", EMAIL); page.fill("#password", "senha123")
    page.click("button[type=submit]"); page.wait_for_url("**/inicio.html")
    uid = page.evaluate("localStorage.getItem('usuarioId')")
    cat = sql("SELECT id_categoria FROM categoria WHERE nome='alimentação'")
    limite = lambda: sql(f"SELECT COUNT(*) FROM alerta WHERE id_usuario={uid} AND tipo='limite'")

    def gasto_pela_tela(descricao, valor):
        page.goto(f"{BASE}/gastos.html")
        page.wait_for_function("document.querySelector('#categoria').options.length > 1")
        page.click("#btnShowAddForm")
        page.fill("#descricao", descricao); page.fill("#valor", str(valor))
        page.select_option("#categoria", cat); page.fill("#data", str(HOJE))
        antes = len(alertas)
        page.click("#formGasto button[type=submit]")
        page.wait_for_function(f"document.body.innerText.includes('{descricao}')")
        page.wait_for_timeout(300)
        return alertas[antes:]

    gasto_pela_tela("Mercado", 500)                                   # 50%: sem alerta
    ok(limite() == "0", "abaixo de 80%: nenhum alerta")
    avisos = gasto_pela_tela("Feira", 350)                            # 85%
    ok(limite() == "1" and any("próximo" in a for a in avisos), "85%: 1 alerta de proximidade")
    for i in range(3):
        gasto_pela_tela(f"Padaria {i}", 10)                           # 86%, 87%, 88%
    ok(limite() == "1", "mais 3 gastos acima de 80%: continua 1 alerta (antes: 4)")
    gasto_pela_tela("Restaurante", 200)                               # 108%
    ok(limite() == "2", "passou de 100%: 1 alerta de limite ultrapassado")
    gasto_pela_tela("Lanche", 15)
    ok(limite() == "2", "outro gasto acima do limite: sem novo alerta")

    page.goto(f"{BASE}/alertas.html"); page.wait_for_timeout(1500)
    corpo = page.inner_text("body").lower()
    ok(corpo.count("próximo do seu limite") == 1 and corpo.count("limite de gastos foi ultrapassado") == 1,
       "tela de alertas mostra um de cada")

    print("ERROS DE PÁGINA:", erros or "nenhum")
    ok(not erros, "nenhum erro de JavaScript")
    nav.close()
