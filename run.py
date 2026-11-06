"""
Executar com: python run.py

O banco só é verificado/instalado ao executar este arquivo diretamente;
importar run.py (por exemplo, `flask --app run`) não toca no banco.
"""
import sys

from backend import create_app

app = create_app()


def main():
    from setup_db import ErroInstalacao, criar_banco

    try:
        if criar_banco():
            print("Banco do Poupe+ criado automaticamente!")
    except ErroInstalacao as erro:
        print(f"Servidor não iniciado: {erro}", file=sys.stderr)
        return 1
    app.run(
        host="127.0.0.1", port=5000, debug=app.config["DEBUG"],
        use_debugger=False, use_reloader=False,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
