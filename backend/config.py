import os
import secrets
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Ativação explícita somente para desenvolvimento local.
    DEBUG = os.getenv("POUPE_DEBUG", "false").strip().lower() == "true"
    IA_LIMITE_MINUTO = int(os.getenv("IA_LIMITE_MINUTO", "5"))
    IA_LIMITE_DIA = int(os.getenv("IA_LIMITE_DIA", "50"))
    IA_LIMITE_GLOBAL_MINUTO = int(os.getenv("IA_LIMITE_GLOBAL_MINUTO", "30"))
    IA_LIMITE_GLOBAL_DIA = int(os.getenv("IA_LIMITE_GLOBAL_DIA", "500"))
    # REV-005: corpo de requisição de no máximo 1 MB (acima disso, 413).
    MAX_CONTENT_LENGTH = 1024 * 1024
    # REV-001: falhas de login (e de senha atual) por e-mail e por IP na janela;
    # cadastros por IP por hora. Passou disso, 429 com Retry-After.
    LOGIN_FALHAS_EMAIL = int(os.getenv("LOGIN_FALHAS_EMAIL", "5"))
    LOGIN_FALHAS_IP = int(os.getenv("LOGIN_FALHAS_IP", "30"))
    LOGIN_JANELA_MINUTOS = int(os.getenv("LOGIN_JANELA_MINUTOS", "15"))
    CADASTROS_IP_HORA = int(os.getenv("CADASTROS_IP_HORA", "10"))
    # Recuperação de senha por e-mail. APP_URL é o endereço que vai no link do
    # e-mail (nunca vem da requisição). Sem SMTP_HOST, a rota responde 503 — ou,
    # com POUPE_DEBUG=true, mostra o link no terminal para testes.
    APP_URL = os.getenv("APP_URL", "http://127.0.0.1:5000")
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USUARIO = os.getenv("SMTP_USUARIO", "")
    SMTP_SENHA = os.getenv("SMTP_SENHA", "")
    SMTP_REMETENTE = os.getenv("SMTP_REMETENTE", "")
    SMTP_SSL = os.getenv("SMTP_SSL", "false").lower() == "true"   # true na porta 465
    SENHA_PEDIDOS_EMAIL_HORA = int(os.getenv("SENHA_PEDIDOS_EMAIL_HORA", "3"))
    SENHA_PEDIDOS_IP_HORA = int(os.getenv("SENHA_PEDIDOS_IP_HORA", "10"))
    # Sem configuração, reiniciar o servidor encerra as sessões locais.
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Strict"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_REFRESH_EACH_REQUEST = False
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "poupe")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
