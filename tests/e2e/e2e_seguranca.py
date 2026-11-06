"""E2E de REV-001 a REV-003: navegador real + Flask + MySQL/MariaDB.

NÃO rodar contra o banco real. Mesmos pré-requisitos e variáveis de
tests/e2e/e2e_recorrencias.py (banco DESCARTÁVEL; MYSQL_DATABASE diferente de "poupe").
Banco já existente: rodar antes `python setup_db.py --atualizar` nele.
"""
import datetime as dt
import os

from playwright.sync_api import sync_playwright

BASE = os.getenv("POUPE_URL", "http://127.0.0.1:5000")
if os.getenv("MYSQL_DATABASE", "poupe_e2e") == "poupe":
    raise SystemExit("Use um banco descartável (MYSQL_DATABASE diferente de 'poupe').")
EMAIL = f"seg{dt.datetime.now():%H%M%S%f}@teste.com"
PAGINAS = ["inicio", "gastos", "receitas", "alertas", "metas", "cofrinho", "orcamento",
           "recorrencia", "relatorios", "score", "desperdicio", "caixa", "caixa (1)",
           "ia", "configuracoes"]
erros, alertas, externos = [], [], []


def ok(cond, msg):
    print(("OK   " if cond else "FALHA ") + msg)
    if not cond:
        raise SystemExit(1)


def entrar(page, senha):
    page.goto(f"{BASE}/login.html")
    page.fill("#email", EMAIL); page.fill("#password", senha)
    page.click("button[type=submit]")


def observar(page):
    page.on("pageerror", lambda e: erros.append(f"{page.url}: {e}"))
    # 401/404 de recursos (logins errados, favicon) não interessam; violação de CSP sim.
    page.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text
            and erros.append(f"{page.url}: {m.text}"))
    page.on("dialog", lambda d: (alertas.append(d.message), d.accept()))
    page.on("request", lambda r: not r.url.startswith(BASE) and externos.append(r.url))


with sync_playwright() as p:
    chrome = os.getenv("CHROME_PATH")
    nav = p.chromium.launch(executable_path=chrome, args=["--no-sandbox"]) if chrome else p.chromium.launch()
    ctx = nav.new_context()
    page = ctx.new_page()
    observar(page)

    page.goto(f"{BASE}/cadastro.html")
    page.fill("#name", "Seg"); page.fill("#email", EMAIL); page.fill("#password", "senha123")
    page.fill("#income", "3000"); page.fill("#limit", "800")
    page.click("button[type=submit]"); page.wait_for_url("**/login.html")

    # REV-001: 5 senhas erradas → 6ª tentativa (mesmo com a certa) recusada
    for _ in range(5):
        entrar(page, "errada"); page.wait_for_timeout(300)
    entrar(page, "senha123"); page.wait_for_timeout(500)
    ok(page.url.endswith("login.html") and "Muitas tentativas" in alertas[-1],
       f"6ª tentativa bloqueada na tela: {alertas[-1]!r}")
    import subprocess
    subprocess.run(["mysql", "-uteste", "-h127.0.0.1", os.getenv("MYSQL_DATABASE", "poupe_e2e"), "-e",
                    "DELETE FROM tentativa_acesso WHERE chave LIKE 'login:%'"],
                   env={**os.environ, "MYSQL_PWD": os.getenv("MYSQL_PASSWORD", "")}, check=True)
    entrar(page, "senha123"); page.wait_for_url("**/inicio.html")
    ok(True, "login liberado depois que a janela passa (tentativas apagadas)")

    # REV-003: todas as páginas, só scripts locais, sem violação de CSP, ícones e gráficos reais
    for nome in PAGINAS:
        page.goto(f"{BASE}/{nome}.html"); page.wait_for_load_state("networkidle")
        icones = page.locator("svg.lucide").count()
        ok(icones > 0, f"{nome}: {icones} ícones lucide desenhados")
        if nome in ("inicio", "relatorios"):
            graficos = page.evaluate("Object.keys(Chart.instances).length")
            ok(graficos > 0, f"{nome}: {graficos} gráfico(s) Chart.js")
    csp = page.goto(f"{BASE}/inicio.html").headers.get("content-security-policy", "")
    ok("script-src 'self'" in csp, "cabeçalho CSP presente")
    ok(not externos, f"nenhuma requisição a outra origem ({externos[:3]})")
    ok(not erros, f"sem erros de página/console/CSP ({erros[:3]})")

    # REV-002: troca de senha pela tela
    outro = nav.new_context(); p2 = outro.new_page(); observar(p2)
    entrar(p2, "senha123"); p2.wait_for_url("**/inicio.html")

    page.goto(f"{BASE}/configuracoes.html"); page.click("#btn-seguranca")
    page.fill("#seg-senha-atual", "errada"); page.fill("#seg-senha-nova", "nova4567")
    page.fill("#seg-senha-confirma", "nova4567"); page.click("text=Alterar senha")
    page.wait_for_timeout(500)
    ok("Senha atual incorreta" in alertas[-1], f"senha atual errada recusada: {alertas[-1]!r}")
    page.fill("#seg-senha-atual", "senha123"); page.click("text=Alterar senha")
    page.wait_for_timeout(500)
    ok("Senha alterada com sucesso" in alertas[-1], "senha alterada pela tela")

    p2.goto(f"{BASE}/gastos.html"); p2.wait_for_url("**/login.html", timeout=5000)
    ok(True, "outro aparelho foi desconectado e voltou ao login")

    # Perfil: trocar e-mail sem senha atual é barrado na tela
    page.goto(f"{BASE}/configuracoes.html"); page.click("#btn-perfil")
    page.wait_for_function("document.getElementById('perfil-email').value !== ''")
    page.fill("#perfil-email", "novo-" + EMAIL); page.click("text=Salvar alterações")
    page.wait_for_timeout(300)
    ok("digite sua senha atual" in alertas[-1], "troca de e-mail pede senha atual")
    page.fill("#perfil-senha-atual", "nova4567"); page.click("text=Salvar alterações")
    page.wait_for_timeout(500)
    ok("salvas com sucesso" in alertas[-1], "e-mail trocado com a senha atual")
    EMAIL = "novo-" + EMAIL

    # Logout: cookie copiado antes deixa de valer
    copia = ctx.cookies()
    page.goto(f"{BASE}/configuracoes.html")
    page.click(".logout-card"); page.wait_for_url("**/login.html")
    ladrao = nav.new_context(); ladrao.add_cookies(copia)
    r = ladrao.request.get(f"{BASE}/sessao")
    ok(r.status == 401, f"cookie copiado após logout → {r.status}")

    entrar(page, "nova4567"); page.wait_for_url("**/inicio.html")
    ok(True, "login com o e-mail e a senha novos")
    nav.close()
print("TUDO OK")
