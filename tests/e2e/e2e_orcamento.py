"""E2E do item 10b (orçamentos no servidor): navegador real + Flask + MySQL/MariaDB.

NÃO rodar contra o banco real: cria usuário, gastos, orçamentos e alertas.
Mesmos pré-requisitos e variáveis de tests/e2e/e2e_recorrencias.py
(banco DESCARTÁVEL; MYSQL_DATABASE diferente de "poupe").
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
MES_PASSADO = HOJE.replace(day=1) - dt.timedelta(days=1)
EMAIL = f"orc{dt.datetime.now():%H%M%S%f}@teste.com"
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


def cartao(page, categoria):
    return page.locator("#orcamentosList .table-card", has_text=categoria).inner_text()


with sync_playwright() as p:
    chrome = os.getenv("CHROME_PATH")
    nav = p.chromium.launch(executable_path=chrome, args=["--no-sandbox"]) if chrome else p.chromium.launch()
    # wait_for_function avalia texto no navegador; a CSP (REV-003) bloqueia eval.
    page = nav.new_page(bypass_csp=True)
    page.route("https://unpkg.com/**", lambda r: r.fulfill(
        content_type="application/javascript", body="window.lucide={createIcons(){}};"))
    page.on("pageerror", lambda e: erros.append(f"{page.url}: {e}"))
    page.on("console", lambda m: m.type == "error" and "net::ERR" not in m.text
            and erros.append(f"{page.url}: {m.text}"))
    page.on("dialog", lambda d: (alertas.append(d.message), d.accept()))

    page.goto(f"{BASE}/cadastro.html")
    page.fill("#name", "Orc"); page.fill("#email", EMAIL); page.fill("#password", "senha123")
    page.fill("#income", "5000"); page.fill("#limit", "2000")
    page.click("button[type=submit]"); page.wait_for_url("**/login.html")
    page.fill("#email", EMAIL); page.fill("#password", "senha123")
    page.click("button[type=submit]"); page.wait_for_url("**/inicio.html")
    uid = page.evaluate("localStorage.getItem('usuarioId')")
    ok(bool(uid), f"login, usuarioId={uid}")

    id_alim = int(sql("SELECT id_categoria FROM categoria WHERE nome='alimentação'"))
    id_educ = int(sql("SELECT id_categoria FROM categoria WHERE nome='educação'"))
    # Gastos: 420 neste mês e 1000 no mês passado (não pode contar)
    page.evaluate(f"""async () => {{
      await GastoAPI.criar({{id_categoria: {id_alim}, valor: 420, data: '{HOJE}', descricao: 'Mercado'}});
      await GastoAPI.criar({{id_categoria: {id_alim}, valor: 1000, data: '{MES_PASSADO}', descricao: 'Antigo'}});
    }}""")
    # Limites antigos só no navegador
    page.evaluate(f"""localStorage.setItem('poupe_orcamentos_u{uid}', JSON.stringify([
      {{id: 1, categoria: 'Alimentação', limite: 500}},
      {{id: 2, categoria: 'Estudos', limite: 200}},
      {{id: 3, categoria: 'Viagem', limite: 100}}]))""")

    # 1. Abrir orçamento: migra, mostra números do servidor (só o mês)
    page.goto(f"{BASE}/orcamento.html")
    page.wait_for_function("document.querySelector('#orcamentosList').innerText.includes('Educação')")
    alim = cartao(page, "Alimentação")
    ok("R$ 420.00" in alim and "(84%)" in alim and "Atenção" in alim, "Alimentação: 420 de 500 (84%), gasto do mês passado ignorado")
    ok("(0%)" in cartao(page, "Educação"), "'Estudos' migrado como Educação")
    ok("Viagem" in page.inner_text("#alertasContainer"), "categoria sem par continua pendente no navegador")
    ok(sql(f"SELECT COUNT(*) FROM orcamento_categoria WHERE id_usuario={uid}") == "2", "2 limites no MySQL")
    page.wait_for_timeout(800)
    ok(sql(f"SELECT COUNT(*) FROM alerta WHERE id_usuario={uid} AND tipo='orcamento'") == "1", "alerta de orçamento registrado")

    # 2. Redefinir Alimentação para 400 pelo formulário (substitui, não duplica)
    page.click("#btnShowAddForm")
    page.select_option("#catOrcamento", str(id_alim))
    page.fill("#limiteValor", "400")
    page.click("#formOrcamento button[type=submit]")
    page.wait_for_function("document.querySelector('#orcamentosList').innerText.includes('(105%)')")
    ok("Estourado" in cartao(page, "Alimentação"), "novo limite 400 → 105% estourado")
    ok(sql(f"SELECT COUNT(*) FROM orcamento_categoria WHERE id_usuario={uid}") == "2", "redefinir não duplica")

    # 3. Recarregar: sem duplicar limites; alerta novo só para a nova situação
    page.reload(); page.wait_for_function("document.querySelector('#orcamentosList').innerText.includes('(105%)')")
    page.wait_for_timeout(800)
    ok(sql(f"SELECT COUNT(*) FROM orcamento_categoria WHERE id_usuario={uid}") == "2", "recarregar não duplica")
    ok(sql(f"SELECT COUNT(*) FROM alerta WHERE id_usuario={uid} AND tipo='orcamento'") == "2", "alertas sem repetição no mesmo dia")

    # 4. Excluir Educação (servidor) e Viagem (local)
    page.locator("#orcamentosList .table-card", has_text="Educação").locator(".delete-btn").click()
    page.wait_for_function("!document.querySelector('#orcamentosList').innerText.includes('Educação')")
    ok(sql(f"SELECT COUNT(*) FROM orcamento_categoria WHERE id_usuario={uid}") == "1", "exclusão remove do MySQL")
    page.locator("#alertasContainer .delete-btn").click()
    page.wait_for_function("!document.querySelector('#alertasContainer').innerText.includes('Viagem')")
    ok(True, "pendente local excluído")

    # 5. Score usa o gasto do mês do servidor (420 > 400 → estourado)
    page.goto(f"{BASE}/score.html"); page.wait_for_timeout(1500)
    ok("Limites estourados" in page.inner_text("body"), "score reconhece orçamento estourado")

    print("ALERTAS:", alertas)
    print("ERROS DE CONSOLE/PÁGINA:", erros or "nenhum")
    ok(not erros, "nenhum erro de JavaScript")
    nav.close()
