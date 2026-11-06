"""E2E do item 10c, parte 2: contas do caixa, metas, cofrinhos e receitas fixas.

Navegador real + Flask + MySQL/MariaDB. NÃO rodar contra o banco real.
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
EMAIL = f"fin{dt.datetime.now():%H%M%S%f}@teste.com"
erros, alertas, respostas = [], [], []


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
    page.route("https://cdn.jsdelivr.net/npm/chart.js*", lambda r: r.fulfill(
        content_type="application/javascript",
        body="window.Chart=function(){return{destroy(){},update(){}}};"))
    page.on("pageerror", lambda e: erros.append(f"{page.url}: {e}"))
    page.on("console", lambda m: m.type == "error" and "net::ERR" not in m.text
            and erros.append(f"{page.url}: {m.text}"))
    # O prompt do aporte recebe o valor configurado em `respostas`.
    page.on("dialog", lambda d: (alertas.append(d.message),
                                 d.accept(respostas.pop(0) if d.type == "prompt" and respostas else None)))

    page.goto(f"{BASE}/cadastro.html")
    page.fill("#name", "Fin"); page.fill("#email", EMAIL); page.fill("#password", "senha123")
    page.fill("#income", "5000"); page.fill("#limit", "2000")
    page.click("button[type=submit]"); page.wait_for_url("**/login.html")
    page.fill("#email", EMAIL); page.fill("#password", "senha123")
    page.click("button[type=submit]"); page.wait_for_url("**/inicio.html")
    uid = page.evaluate("localStorage.getItem('usuarioId')")
    ok(bool(uid), f"login, usuarioId={uid}")
    conta = lambda t: int(sql(f"SELECT COUNT(*) FROM {t} WHERE id_usuario={uid}"))

    # Dados antigos que só existiam no navegador
    page.evaluate(f"""() => {{
      localStorage.setItem('poupe_contas_u{uid}', JSON.stringify([{{id: 1, nome: 'Nubank', tipo: 'Corrente', saldo: 1500}}]));
      localStorage.setItem('poupe_cofrinhos_u{uid}', JSON.stringify([{{id: 2, titulo: 'Reserva', alvo: 1000, prazoMeses: 10, guardado: 100}}]));
      localStorage.setItem('poupePlus_goals_u{uid}', JSON.stringify([{{title: 'Viagem', target: 5000, current: 1200}}]));
    }}""")

    # ---- Caixa / contas -------------------------------------------------------
    page.goto(f"{BASE}/caixa.html")
    page.wait_for_function("document.querySelector('#contasList').innerText.includes('Nubank')")
    page.wait_for_timeout(300)
    ok(conta("conta") == 1, "conta antiga migrada para o MySQL")
    ok("1.500,00" in page.inner_text("#saldoTotalGeral"), "saldo total exibido")
    page.click("#btnShowAddForm")
    page.fill("#nomeConta", "Carteira"); page.select_option("#tipoConta", "Dinheiro Físico"); page.fill("#saldoInicial", "250,50")
    page.click("#formConta button[type=submit]")
    page.wait_for_function("document.querySelector('#contasList').innerText.includes('Carteira')")
    ok(conta("conta") == 2 and "1.750,50" in page.inner_text("#saldoTotalGeral"), "nova conta no MySQL e saldo somado")
    page.locator("#contasList tr", has_text="Carteira").locator(".delete-btn").click()
    page.wait_for_function("!document.querySelector('#contasList').innerText.includes('Carteira')")
    ok(conta("conta") == 1, "exclusão de conta remove do MySQL")

    # ---- Metas ------------------------------------------------------------------
    page.goto(f"{BASE}/metas.html")
    page.wait_for_function("document.querySelector('#goalsGrid').innerText.includes('Viagem')")
    page.wait_for_timeout(300)
    ok(conta("meta") == 1, "meta antiga migrada (tela antes quebrava ao abrir)")
    page.click(".btn-add")
    page.fill("#goalTitle", "Celular"); page.fill("#targetValue", "3000"); page.fill("#currentValue", "750")
    page.click("#goalForm button[type=submit]")
    page.wait_for_function("document.querySelector('#goalsGrid').innerText.includes('Celular')")
    ok(conta("meta") == 2, "nova meta no MySQL")
    page.reload(); page.wait_for_function("document.querySelector('#goalsGrid').innerText.includes('Celular')")
    ok("25%" in page.locator(".goal-card", has_text="Celular").inner_text(), "meta persiste após recarregar (antes sumia)")
    page.locator(".goal-card", has_text="Celular").locator(".delete-btn").click()
    page.wait_for_function("!document.querySelector('#goalsGrid').innerText.includes('Celular')")
    ok(conta("meta") == 1, "exclusão de meta remove do MySQL")

    # ---- Cofrinhos ----------------------------------------------------------------
    page.goto(f"{BASE}/cofrinho.html")
    page.wait_for_function("document.querySelector('#cofrinhosList').innerText.includes('Reserva')")
    page.wait_for_timeout(300)
    ok(conta("cofrinho") == 1, "cofrinho antigo migrado")
    respostas.append("50,25")
    page.locator("#cofrinhosList .table-card", has_text="Reserva").locator(".add-valor-btn").click()
    page.wait_for_function("document.querySelector('#cofrinhosList').innerText.includes('150.25')")
    ok(sql(f"SELECT valor_guardado FROM cofrinho WHERE id_usuario={uid}") == "150.25", "aporte somado no MySQL")
    page.click("#btnShowAddForm")
    page.fill("#tituloMeta", "Carro"); page.fill("#metaValor", "20000"); page.fill("#prazoMeses", "24"); page.fill("#metaGuardado", "0")
    page.click("#formCofrinho button[type=submit]")
    page.wait_for_function("document.querySelector('#cofrinhosList').innerText.includes('Carro')")
    ok(conta("cofrinho") == 2, "novo cofrinho no MySQL")
    page.locator("#cofrinhosList .table-card", has_text="Carro").locator(".delete-btn").click()
    page.wait_for_function("!document.querySelector('#cofrinhosList').innerText.includes('Carro')")
    ok(conta("cofrinho") == 1, "exclusão de cofrinho remove do MySQL")

    # ---- Receita fixa gera receita no dia ---------------------------------------------
    page.goto(f"{BASE}/recorrencia.html"); page.wait_for_timeout(800)
    page.click("#btnShowAddForm"); page.select_option("#recTipo", "Receita Fixa")
    page.select_option("#recCategoriaReceita", "Salário")
    page.fill("#recDescricao", "Salário empresa"); page.fill("#recValor", "4200"); page.fill("#recDia", str(HOJE.day))
    page.click("#formRecorrencia button[type=submit]")
    page.wait_for_function("document.querySelector('#recorrenciasList').innerText.includes('Salário empresa')")
    ok(conta("receita_recorrente") == 1, "receita fixa no MySQL")
    page.goto(f"{BASE}/receitas.html")
    page.wait_for_function("document.querySelector('#incomesTableBody').innerText.includes('Salário empresa')")
    ok(sql(f"SELECT COUNT(*) FROM receita WHERE id_usuario={uid} AND data='{HOJE}'") == "1",
       "receita do dia gerada automaticamente")
    page.reload(); page.wait_for_timeout(1000)
    ok(conta("receita") == 1, "processar de novo não duplica a receita")

    # ---- Radar do caixa com receita fixa e outras telas sem erro ----------------------
    for tela in ["caixa.html", "score.html", "relatorios.html", "orcamento.html", "desperdicio.html"]:
        page.goto(f"{BASE}/{tela}"); page.wait_for_timeout(1000)

    print("ALERTAS:", alertas)
    print("ERROS DE CONSOLE/PÁGINA:", erros or "nenhum")
    ok(not erros, "nenhum erro de JavaScript")
    nav.close()
