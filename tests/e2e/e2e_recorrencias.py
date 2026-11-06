"""E2E do item 10a: navegador real + Flask + MySQL/MariaDB.

NÃO rodar contra o banco real: cria usuário, recorrências e gastos.
Pré-requisitos: pip install playwright; Chrome/Chromium instalado; servidor
rodando com um banco DESCARTÁVEL e vazio, por exemplo:

    set MYSQL_DATABASE=poupe_e2e   (Linux/macOS: export ...)
    python setup_db.py && python run.py
    python tests/e2e/e2e_recorrencias.py

Variáveis: MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DATABASE (padrão
poupe_e2e; recusa "poupe"), CHROME_PATH (opcional), POUPE_URL.
lucide e Chart.js são servidos de frontend/vendor/ (sem internet). Cada script
cadastra um usuário: para rodar todos, suba o servidor com CADASTROS_IP_HORA=1000
(o padrão, 10 por hora por IP, é o limite do REV-001).
"""
import datetime as dt
import json
import os
import subprocess

from playwright.sync_api import sync_playwright

BASE = os.getenv("POUPE_URL", "http://127.0.0.1:5000")
BANCO = os.getenv("MYSQL_DATABASE", "poupe_e2e")
if BANCO == "poupe":
    raise SystemExit("Use um banco descartável (MYSQL_DATABASE diferente de 'poupe').")
HOJE = dt.date.today()
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
        content_type="application/javascript", body="window.lucide={createIcons(){}};"))
    page.on("pageerror", lambda e: erros.append(f"{page.url}: {e}"))
    # Falhas de rede de recursos externos (CDN) não contam como erro do código.
    page.on("console", lambda m: m.type == "error" and "net::ERR" not in m.text
            and erros.append(f"{page.url}: {m.text}"))
    page.on("dialog", lambda d: (alertas.append(d.message), d.accept()))

    # Cadastro + login pela interface
    page.goto(f"{BASE}/cadastro.html")
    page.fill("#name", "Teste"); page.fill("#email", EMAIL); page.fill("#password", "senha123")
    page.fill("#income", "5000"); page.fill("#limit", "2000")
    page.click("button[type=submit]"); page.wait_for_url("**/login.html")
    page.fill("#email", EMAIL); page.fill("#password", "senha123")
    page.click("button[type=submit]"); page.wait_for_url("**/inicio.html")
    uid = page.evaluate("localStorage.getItem('usuarioId')")
    ok(bool(uid), f"login, usuarioId={uid}")

    # Dados antigos só no navegador: gasto fixo vencendo hoje + receita fixa
    page.evaluate(f"""localStorage.setItem('poupe_recorrencias_u{uid}', JSON.stringify([
      {{id: 1, descricao: 'Aluguel', tipo: 'Gasto Fixo', valor: 1200, dia: '{HOJE.day}'}},
      {{id: 2, descricao: 'Salário', tipo: 'Receita Fixa', valor: 5000, dia: '5'}}]))""")

    # 1. Abrir recorrências: migra o gasto fixo e mostra as duas
    page.goto(f"{BASE}/recorrencia.html")
    page.wait_for_function("document.querySelector('#recorrenciasList').innerText.includes('Gasto Fixo · Outros')")
    texto = page.inner_text("#recorrenciasList")
    ok("Aluguel" in texto and "Receita Fixa · Outros" in texto, "gasto fixo e receita fixa migrados aparecem")
    ok(any("enviadas ao servidor" in a for a in alertas), "aviso de migração exibido")
    ok(sql(f"SELECT COUNT(*) FROM recorrencia_gasto WHERE id_usuario={uid}") == "1", "gasto fixo migrado para o MySQL")
    ok(sql(f"SELECT COUNT(*) FROM receita_recorrente WHERE id_usuario={uid}") == "1", "receita fixa migrada para o MySQL (item 10c)")
    ok(sql(f"SELECT COUNT(*) FROM gasto WHERE id_usuario={uid} AND recorrente=1") == "1", "gasto do dia gerado pelo processamento")

    # 2. Cadastrar gasto fixo novo pelo formulário (alimentação, dia 28)
    page.click("#btnShowAddForm")
    page.fill("#recDescricao", "Mercado mensal"); page.select_option("#recTipo", "Gasto Fixo")
    page.select_option("#recCategoria", label="Alimentação")
    page.fill("#recValor", "450,50"); page.fill("#recDia", "28")
    page.click("#formRecorrencia button[type=submit]")
    page.wait_for_function("document.querySelector('#recorrenciasList').innerText.includes('Mercado mensal')")
    ok(sql(f"SELECT descricao, valor, frequencia, dia_mes FROM recorrencia_gasto WHERE id_usuario={uid} AND descricao='Mercado mensal'")
       == "Mercado mensal\t450.50\tmensal\t28", "novo gasto fixo salvo no MySQL")

    # 3. Receita fixa nova vai para o servidor com categoria de receita
    page.click("#btnShowAddForm"); page.select_option("#recTipo", "Receita Fixa")
    ok(page.is_hidden("#grupoCategoria") and page.is_visible("#grupoCategoriaReceita"),
       "categoria de gasto oculta e de receita visível para receita fixa")
    page.select_option("#recCategoriaReceita", "Trabalho")
    page.fill("#recDescricao", "Freela"); page.fill("#recValor", "800"); page.fill("#recDia", "28")
    page.click("#formRecorrencia button[type=submit]")
    page.wait_for_function("document.querySelector('#recorrenciasList').innerText.includes('Freela')")
    ok(sql(f"SELECT COUNT(*) FROM recorrencia_gasto WHERE id_usuario={uid}") == "2", "receita fixa não entrou como gasto")
    ok(sql(f"SELECT categoria, dia_mes FROM receita_recorrente WHERE id_usuario={uid} AND descricao='Freela'") == "Trabalho\t28",
       "receita fixa salva no MySQL com categoria e dia")

    # 4. Recarregar não duplica nada
    page.reload(); page.wait_for_function("document.querySelector('#recorrenciasList').innerText.includes('Freela')")
    ok(sql(f"SELECT COUNT(*) FROM gasto WHERE id_usuario={uid}") == "1" and sql(f"SELECT COUNT(*) FROM recorrencia_gasto WHERE id_usuario={uid}") == "2"
       and sql(f"SELECT COUNT(*) FROM receita_recorrente WHERE id_usuario={uid}") == "2", "recarregar não duplica")

    # 5. Gastos mostra o gasto gerado
    page.goto(f"{BASE}/gastos.html"); page.wait_for_timeout(1500)
    ok("Aluguel" in page.inner_text("body"), "gastos.html lista o gasto gerado pela recorrência")

    # 6. Excluir recorrência do servidor pela tela
    page.goto(f"{BASE}/recorrencia.html")
    page.wait_for_function("document.querySelector('#recorrenciasList').innerText.includes('Mercado mensal')")
    linha = page.locator("tr", has_text="Mercado mensal")
    linha.locator(".delete-btn").click()
    page.wait_for_function("!document.querySelector('#recorrenciasList').innerText.includes('Mercado mensal')")
    ok(sql(f"SELECT COUNT(*) FROM recorrencia_gasto WHERE id_usuario={uid}") == "1", "exclusão remove do MySQL")

    # 7. Telas leitoras abrem sem erro e com cópias atualizadas
    page.evaluate(f"localStorage.removeItem('poupe_gastos_u{uid}')")   # força depender da sincronização
    for tela in ["orcamento.html", "score.html", "cofrinho.html", "desperdicio.html", "caixa.html"]:
        page.goto(f"{BASE}/{tela}"); page.wait_for_timeout(1200)
    gastos = json.loads(page.evaluate(f"localStorage.getItem('poupe_gastos_u{uid}')") or "[]")
    ok(len(gastos) == 1 and gastos[0]["descricao"] == "Aluguel", "cache de gastos refeito ao abrir telas leitoras")
    rec = json.loads(page.evaluate(f"localStorage.getItem('poupe_recorrencias_u{uid}')"))
    ok(sorted(r["descricao"] for r in rec) == ["Aluguel", "Freela", "Salário"]
       and all(r.get("origem") == "servidor" for r in rec), "cache de recorrências: tudo vindo do servidor")
    ok(page.inner_text("#radarDiasDura").endswith("dias"), "radar do caixa renderizado")

    print("ALERTAS:", alertas)
    print("ERROS DE CONSOLE/PÁGINA:", erros or "nenhum")
    ok(not erros, "nenhum erro de JavaScript")
    nav.close()
