"""E2E do item 10c (receitas no servidor): navegador real + Flask + MySQL/MariaDB.

NÃO rodar contra o banco real: cria usuário e receitas.
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
EMAIL = f"rec{dt.datetime.now():%H%M%S%f}@teste.com"
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
        # Stub do lucide: preenche os ícones para botões só-ícone terem tamanho (clicáveis).
        body="window.lucide={createIcons(){document.querySelectorAll('[data-lucide]:empty')"
             ".forEach(e=>e.textContent='•')}};"))
    # Chart.js também vem de CDN; o stub evita erro quando não há internet.
    page.route("https://cdn.jsdelivr.net/npm/chart.js*", lambda r: r.fulfill(
        content_type="application/javascript",
        body="window.Chart=function(){return{destroy(){},update(){}}};"))
    page.on("pageerror", lambda e: erros.append(f"{page.url}: {e}"))
    page.on("console", lambda m: m.type == "error" and "net::ERR" not in m.text
            and erros.append(f"{page.url}: {m.text}"))
    page.on("dialog", lambda d: (alertas.append(d.message), d.accept()))

    page.goto(f"{BASE}/cadastro.html")
    page.fill("#name", "Rec"); page.fill("#email", EMAIL); page.fill("#password", "senha123")
    page.fill("#income", "5000"); page.fill("#limit", "2000")
    page.click("button[type=submit]"); page.wait_for_url("**/login.html")
    page.fill("#email", EMAIL); page.fill("#password", "senha123")
    page.click("button[type=submit]"); page.wait_for_url("**/inicio.html")
    uid = page.evaluate("localStorage.getItem('usuarioId')")
    ok(bool(uid), f"login, usuarioId={uid}")
    contar = lambda: int(sql(f"SELECT COUNT(*) FROM receita WHERE id_usuario={uid}"))

    # Receitas antigas só no navegador + chave sem usuário (bug antigo da exclusão)
    page.evaluate(f"""() => {{
      localStorage.setItem('poupePlus_incomes_u{uid}', JSON.stringify([
        {{description: 'Salário', category: 'Salário', amount: 5000, date: '{HOJE}'}},
        {{description: 'Bônus antigo', category: 'Outros', amount: 300, date: '{MES_PASSADO}'}},
        {{description: 'Sem valor', category: 'Outros', amount: 0, date: '{HOJE}'}}]));
      localStorage.setItem('poupePlus_incomes', '[{{"description":"de outra conta"}}]');
    }}""")

    # 1. Abrir: mês atual, migração das válidas
    page.goto(f"{BASE}/receitas.html")
    page.wait_for_function("document.querySelector('#incomesTableBody').innerText.includes('Salário')")
    page.wait_for_timeout(500)
    ok(page.input_value("#monthPicker") == f"{HOJE:%Y-%m}", "abre no mês atual (antes: agosto/2026 fixo)")
    ok(contar() == 2, "2 receitas válidas migradas para o MySQL")
    ok(any("enviadas ao servidor" in a for a in alertas), "aviso de migração exibido")
    corpo = page.inner_text("#incomesTableBody")
    ok("Sem valor (neste navegador)" in corpo, "receita inválida continua local e identificada")
    ok(page.evaluate("localStorage.getItem('poupePlus_incomes')") is None, "chave sem usuário removida")

    # 2. Nova receita pelo formulário, com a data padrão (hoje, fuso local)
    page.click("#btnOpenModal")
    ok(page.input_value("#incomeDate") == f"{HOJE}", "data padrão = hoje no fuso local")
    page.fill("#incomeDesc", "Freela site"); page.select_option("#incomeCategory", "Trabalho")
    page.fill("#incomeValue", "800.50")
    page.click("#incomeForm button[type=submit]")
    page.wait_for_function("document.querySelector('#incomesTableBody').innerText.includes('Freela site')")
    ok(contar() == 3, "nova receita salva no MySQL")
    ok(sql(f"SELECT valor FROM receita WHERE descricao='Freela site' AND id_usuario={uid}") == "800.50", "valor gravado certo")
    ok("5.800,50" in page.inner_text("#totalDisplay"), "total do mês: 5000 + 800,50 (inválida soma 0)")

    # 3. Mês anterior mostra a migrada de lá
    page.click("#prevMonth")
    ok("Bônus antigo" in page.inner_text("#incomesTableBody"), "navegação de mês funciona")
    page.click("#nextMonth")

    # 4. Excluir receita do servidor e confirmar que persiste após recarregar
    page.locator("#incomesTableBody tr", has_text="Freela site").locator(".delete-btn").click()
    page.wait_for_function("!document.querySelector('#incomesTableBody').innerText.includes('Freela site')")
    ok(contar() == 2, "exclusão remove do MySQL")
    page.reload(); page.wait_for_function("document.querySelector('#incomesTableBody').innerText.includes('Salário')")
    ok("Freela site" not in page.inner_text("#incomesTableBody"), "exclusão persiste após recarregar (antes não persistia)")
    ok(contar() == 2, "recarregar não duplica")

    # 5. Excluir a pendente local
    page.locator("#incomesTableBody tr", has_text="Sem valor").locator(".delete-btn").click()
    page.wait_for_function("!document.querySelector('#incomesTableBody').innerText.includes('Sem valor')")
    ok(True, "pendente local excluída")

    # 6. Score e relatórios usam as receitas do servidor mesmo sem cópia local
    page.evaluate(f"localStorage.removeItem('poupePlus_incomes_u{uid}')")
    page.goto(f"{BASE}/score.html"); page.wait_for_timeout(1500)
    ok("Nenhuma receita cadastrada" not in page.inner_text("body"), "score enxerga as receitas")
    page.goto(f"{BASE}/relatorios.html"); page.wait_for_timeout(1500)
    ok(page.evaluate(f"JSON.parse(localStorage.getItem('poupePlus_incomes_u{uid}')).length") == 2,
       "relatórios sincronizam as receitas")

    print("ALERTAS:", alertas)
    print("ERROS DE CONSOLE/PÁGINA:", erros or "nenhum")
    ok(not erros, "nenhum erro de JavaScript")
    nav.close()
