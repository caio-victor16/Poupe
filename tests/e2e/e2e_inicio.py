"""E2E do item 11 (painel inicial): navegador real + Flask + MySQL/MariaDB.

NÃO rodar contra o banco real: cria usuário, gastos, receitas e alertas.
Mesmos pré-requisitos e variáveis de tests/e2e/e2e_recorrencias.py
(banco DESCARTÁVEL; MYSQL_DATABASE diferente de "poupe").
O Chart.js é substituído por um stub que registra os dados dos gráficos.
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
MESES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto',
         'Setembro', 'Outubro', 'Novembro', 'Dezembro']
EMAIL = f"ini{dt.datetime.now():%H%M%S%f}@teste.com"
erros = []


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
    page.route("**/vendor/chart-*.js", lambda r: r.fulfill(
        content_type="application/javascript",
        body="window.__graficos=[];window.Chart=function(el,cfg){const g={cfg,vivo:true,destroy(){g.vivo=false}};"
             "window.__graficos.push(g);return g};"))
    page.on("pageerror", lambda e: erros.append(f"{page.url}: {e}"))
    page.on("console", lambda m: m.type == "error" and "net::ERR" not in m.text
            and erros.append(f"{page.url}: {m.text}"))
    page.on("dialog", lambda d: d.accept())

    page.goto(f"{BASE}/cadastro.html")
    page.fill("#name", "Caio Teste"); page.fill("#email", EMAIL); page.fill("#password", "senha123")
    page.fill("#income", "5000"); page.fill("#limit", "2000")
    page.click("button[type=submit]"); page.wait_for_url("**/login.html")
    page.fill("#email", EMAIL); page.fill("#password", "senha123")
    page.click("button[type=submit]"); page.wait_for_url("**/inicio.html")
    uid = page.evaluate("localStorage.getItem('usuarioId')")
    ok(bool(uid), f"login, usuarioId={uid}")

    alim = sql("SELECT id_categoria FROM categoria WHERE nome='alimentação'")
    transp = sql("SELECT id_categoria FROM categoria WHERE nome='transporte'")
    page.evaluate(f"""async () => {{
      await GastoAPI.criar({{id_categoria: {alim}, valor: 120.10, data: '{HOJE}', descricao: 'Mercado <b>'}});
      await GastoAPI.criar({{id_categoria: {transp}, valor: 30.20, data: '{HOJE}', descricao: 'Uber'}});
      await GastoAPI.criar({{id_categoria: {alim}, valor: 999, data: '{MES_PASSADO}', descricao: 'Mês passado'}});
      await ReceitaAPI.criar({{descricao: 'Salário', categoria: 'Salário', valor: 5000, data: '{HOJE}'}});
      await requisicao('/alertas', 'POST', {{tipo: 'teste', mensagem: 'Alerta não lido'}});
    }}""")

    page.goto(f"{BASE}/inicio.html")
    page.wait_for_function("document.querySelector('#totalExpenses').innerText.includes('150,30')")
    page.wait_for_timeout(800)
    texto = lambda i: page.inner_text(i).replace("\xa0", " ")
    ok(texto("#currentMonthYear") == f"{MESES[HOJE.month - 1]} de {HOJE.year}", "mês atual no cabeçalho (antes: Agosto de 2026 fixo)")
    ok(texto("#totalIncomes") == "R$ 5.000,00", "receitas do mês")
    ok(texto("#totalExpenses") == "R$ 150,30", "gastos do mês (mês passado fora)")
    ok(texto("#balance") == "R$ 4.849,70", "saldo = receitas - gastos")
    ok(texto("#donutTotalDisplay") == "R$ 150,30", "total no centro da rosca")
    legenda = texto("#chartLegend")
    ok("Alimentação" in legenda and "80%" in legenda and "Transporte" in legenda and "20%" in legenda, "legenda por categoria")
    recentes = texto("#recentExpensesList")
    ok("Mercado <b>" in recentes and "Uber" in recentes and "Mês passado" not in recentes,
       "últimos gastos do mês, com HTML escapado")
    ok(page.locator("#recentExpensesList b").count() == 0, "descrição não virou HTML")
    ok("% do mês concluído" in texto("#monthProgressText"), "progresso do mês")
    ok(page.inner_text(".user-greeting h1") == "Olá, Caio 👋" and page.inner_text(".avatar-circle") == "C",
       "nome e inicial do usuário (antes: 'D' fixo)")
    ok("1" in page.inner_text(".icon-btn[title^='Notificações']"), "contador de alertas não lidos")

    graficos = page.evaluate("window.__graficos.filter(g => g.vivo).map(g => g.cfg)")
    rosca = next(g for g in graficos if g["type"] == "doughnut")
    linha = next(g for g in graficos if g["type"] == "line")
    ok(rosca["data"]["labels"] == ["Alimentação", "Transporte"] and rosca["data"]["datasets"][0]["data"] == [120.1, 30.2],
       "dados da rosca")
    valores = linha["data"]["datasets"][0]["data"]
    ok(valores[HOJE.day - 1] == 150.3 and all(v is None for v in valores[HOJE.day:]),
       "evolução acumulada até hoje; dias futuros sem linha")

    page.click("#prevMonthBtn"); page.wait_for_timeout(300)
    ok(texto("#currentMonthYear") == f"{MESES[MES_PASSADO.month - 1]} de {MES_PASSADO.year}", "navega para o mês anterior")
    ok(texto("#totalExpenses") == "R$ 999,00" and texto("#totalIncomes") == "R$ 0,00", "números do mês anterior")
    ok(texto("#monthProgressText") == "100% do mês concluído", "mês passado 100% concluído")
    ok(page.evaluate("window.__graficos.filter(g => g.vivo).length") == 2, "gráficos antigos destruídos ao trocar de mês")
    page.click("#nextMonthBtn"); page.click("#nextMonthBtn"); page.wait_for_timeout(300)
    ok(texto("#totalExpenses") == "R$ 0,00" and texto("#monthProgressText") == "0% do mês concluído",
       "mês futuro vazio e 0%")
    ok("Nenhum gasto" in texto("#recentExpensesList"), "estado vazio")

    page.click(".icon-btn[title^='Notificações']"); page.wait_for_url("**/alertas.html")
    ok(True, "sino leva aos alertas")

    print("ERROS DE CONSOLE/PÁGINA:", erros or "nenhum")
    ok(not erros, "nenhum erro de JavaScript")
    nav.close()
