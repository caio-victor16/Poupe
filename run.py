"""
Executar com: python run.py
"""

from backend import create_app
from setup_db import criar_banco

if criar_banco():
    print("Banco 'poupe' criado automaticamente!")

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
