"""Envio de e-mail por SMTP (ex.: Gmail com "senha de app"). Configuração no .env."""
import smtplib
import threading
from email.message import EmailMessage

from flask import current_app


def smtp_configurado():
    return bool(current_app.config.get("SMTP_HOST"))


def _enviar(cfg, mensagem):
    try:
        if cfg["SMTP_SSL"]:
            servidor = smtplib.SMTP_SSL(cfg["SMTP_HOST"], cfg["SMTP_PORT"], timeout=15)
        else:
            servidor = smtplib.SMTP(cfg["SMTP_HOST"], cfg["SMTP_PORT"], timeout=15)
            servidor.starttls()
        with servidor:
            if cfg["SMTP_USUARIO"]:
                servidor.login(cfg["SMTP_USUARIO"], cfg["SMTP_SENHA"])
            servidor.send_message(mensagem)
    except (OSError, smtplib.SMTPException) as erro:
        # Sem destinatário nem conteúdo no log (o e-mail leva um link secreto).
        cfg["LOGGER"].warning("E-mail: falha no envio (%s)", type(erro).__name__)


def enviar_email(para, assunto, texto):
    """Envia em segundo plano: a resposta HTTP não espera o SMTP e leva o mesmo
    tempo exista ou não a conta (não revela quais e-mails estão cadastrados)."""
    app = current_app
    cfg = {chave: app.config.get(chave) for chave in
           ("SMTP_HOST", "SMTP_PORT", "SMTP_USUARIO", "SMTP_SENHA", "SMTP_SSL")}
    cfg["LOGGER"] = app.logger
    mensagem = EmailMessage()
    mensagem["From"] = app.config.get("SMTP_REMETENTE") or app.config.get("SMTP_USUARIO")
    mensagem["To"] = para
    mensagem["Subject"] = assunto
    mensagem.set_content(texto)
    if app.config.get("TESTING"):
        _enviar(cfg, mensagem)
    else:
        threading.Thread(target=_enviar, args=(cfg, mensagem), daemon=True).start()
