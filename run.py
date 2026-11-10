"""
Executar com:

python run.py

Atualizar banco de dados do app com o comando no terminal:

python setup_db.py --atualizar

O banco só é verificado/instalado ao executar este arquivo diretamente;
importar run.py (por exemplo, `flask --app run`) não toca no banco.

Porta: 5000 por padrão (ou POUPE_PORT no .env). Se ela estiver ocupada ou
bloqueada pelo Windows (erro 10013, "tentativa de acesso a um soquete de uma
maneira que é proibida"), o servidor tenta as portas reserva e mostra o
endereço certo para abrir no navegador.
"""
import os
import socket
import sys

from backend import create_app

app = create_app()

HOST = "127.0.0.1"
PORTAS_RESERVA = (5001, 5050, 8000, 8080, 8765, 9000)


def porta_disponivel(host, porta):
    """True se dá para abrir a porta agora (livre e não bloqueada pelo sistema)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as teste:
        try:
            teste.bind((host, porta))
            return True
        except OSError:          # 10013 (bloqueada/reservada) ou 10048 (em uso)
            return False


def escolher_porta(host, preferida):
    for porta in (preferida, *[p for p in PORTAS_RESERVA if p != preferida]):
        if porta_disponivel(host, porta):
            return porta
    return None


def situacao_ia():
    """Uma linha no terminal dizendo se a IA vai funcionar (nunca mostra a chave)."""
    from backend.config import ARQUIVO_ENV

    chave = (os.getenv("GEMINI_API_KEY") or "").strip().strip("\"'")
    if chave:
        modelo = (os.getenv("GEMINI_MODEL") or "gemini-flash-latest").strip()
        return f"IA: ativada (modelo {modelo})."
    if not ARQUIVO_ENV.exists():
        return f"IA: DESATIVADA — não existe o arquivo {ARQUIVO_ENV}. Crie-o com a linha GEMINI_API_KEY=sua_chave."
    return f"IA: DESATIVADA — falta a linha GEMINI_API_KEY=sua_chave em {ARQUIVO_ENV}."


def main():
    from setup_db import ErroInstalacao, criar_banco

    try:
        if criar_banco():
            print("Banco do Poupe+ criado automaticamente!")
    except ErroInstalacao as erro:
        print(f"Servidor não iniciado: {erro}", file=sys.stderr)
        return 1

    try:
        preferida = int(os.getenv("POUPE_PORT", "5000"))
    except ValueError:
        preferida = 5000
    porta = escolher_porta(HOST, preferida)
    if porta is None:
        print(
            "Servidor não iniciado: nenhuma porta disponível "
            f"({preferida}, {', '.join(map(str, PORTAS_RESERVA))}). "
            "Defina outra em POUPE_PORT no .env.",
            file=sys.stderr,
        )
        return 1
    if porta != preferida:
        print(f"Aviso: a porta {preferida} está ocupada ou bloqueada pelo sistema; usando a {porta}.")

    endereco = f"http://{HOST}:{porta}"
    if not os.getenv("APP_URL"):
        # Link do e-mail de "esqueci a senha" acompanha a porta real.
        app.config["APP_URL"] = endereco
    print(f"Poupe+ rodando. Abra no navegador: {endereco}")
    print(situacao_ia())

    app.run(
        host=HOST, port=porta, debug=app.config["DEBUG"],
        use_debugger=False, use_reloader=False,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
