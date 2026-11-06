"""E2E do item 12 (validações): navegador real + Flask + MySQL/MariaDB.

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
EMAIL = f"val{dt.datetime.now():%H%M%S%f}@teste.com"
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
        content_type="application/javascript", body="window.lucide={createIcons(){}};"))
    page.on("pageerror", lambda e: erros.append(f"{page.url}: {e}"))
    page.on("dialog", lambda d: (alertas.append(d.message), d.accept()))

    # Cadastro pela tela com renda zero (antes: recusado como "campo obrigatório")
    page.goto(f"{BASE}/cadastro.html")
    page.fill("#name", "Renda Zero"); page.fill("#email", EMAIL); page.fill("#password", "senha123")
    page.fill("#income", "0"); page.fill("#limit", "800")
    page.click("button[type=submit]"); page.wait_for_url("**/login.html")
    ok(sql(f"SELECT renda_mensal FROM usuario WHERE email='{EMAIL}'") == "0.00", "cadastro com renda 0 pela tela")

    page.fill("#email", EMAIL); page.fill("#password", "senha123")
    page.click("button[type=submit]"); page.wait_for_url("**/inicio.html")
    uid = page.evaluate("localStorage.getItem('usuarioId')")
    cat = sql("SELECT id_categoria FROM categoria WHERE nome='alimentação'")

    # Chamadas inválidas direto na API, com a sessão real
    status = page.evaluate(f"""async () => {{
      const chamar = async (url, metodo, corpo) => (await fetch(url, {{method: metodo, credentials: 'same-origin',
        headers: {{'Content-Type': 'application/json', 'X-Poupe-Request': '1'}}, body: JSON.stringify(corpo)}})).status;
      const r = {{}};
      r.valorTexto = await chamar('/gastos', 'POST', {{id_categoria: {cat}, valor: 'abc', data: '2026-11-05'}});
      r.categoriaInexistente = await chamar('/gastos', 'POST', {{id_categoria: 9999, valor: 10, data: '2026-11-05'}});
      r.dataInvalida = await chamar('/gastos', 'POST', {{id_categoria: {cat}, valor: 10, data: '2026-02-30'}});
      r.valido = await chamar('/gastos', 'POST', {{id_categoria: {cat}, valor: 10, data: '2026-11-05', descricao: 'ok'}});
      const lista = await (await fetch('/gastos/usuario/{uid}', {{credentials: 'same-origin'}})).json();
      r.putInvalido = await chamar('/gastos/' + lista[0].id_gasto, 'PUT', {{valor: 'abc'}});
      r.periodo = (await fetch('/gastos/usuario/{uid}/periodo?inicio=2026-12-01&fim=2026-11-01')).status;
      r.boletoCurto = await chamar('/boletos', 'POST', {{codigo_barras: '123', valor: 10, vencimento: '2026-12-01'}});
      r.perfilEmail = await chamar('/usuarios/{uid}', 'PUT', {{email: 'invalido'}});
      r.limiteZero = await chamar('/usuarios/{uid}', 'PUT', {{limite_gastos: 0}});
      return r;
    }}""")
    ok(status["valorTexto"] == 400, "gasto com valor texto → 400")
    ok(status["categoriaInexistente"] == 400, "gasto com categoria inexistente → 400 (antes: erro do banco)")
    ok(status["dataInvalida"] == 400, "gasto com 30/02 → 400")
    ok(status["valido"] == 201, "gasto válido → 201")
    ok(status["putInvalido"] == 400, "PUT de gasto inválido → 400 (antes: gravava ou dava 500)")
    ok(sql(f"SELECT valor FROM gasto WHERE id_usuario={uid}") == "10.00", "gasto não foi alterado pelo PUT inválido")
    ok(status["periodo"] == 400, "período invertido → 400 (antes: ia para a procedure)")
    ok(status["boletoCurto"] == 400, "boleto com código curto → 400")
    ok(status["perfilEmail"] == 400 and status["limiteZero"] == 400, "perfil inválido → 400")
    ok(sql(f"SELECT email, limite_gastos FROM usuario WHERE id_usuario={uid}") == f"{EMAIL}\t800.00",
       "perfil não foi alterado")

    print("ERROS DE PÁGINA:", erros or "nenhum")
    ok(not erros, "nenhum erro de JavaScript")
    nav.close()
