"""Sessões revogáveis (REV-002) e limite de tentativas (REV-001).

Os dois ficam no banco principal, então valem para todos os processos do
servidor e sobrevivem a reinícios.
"""
import hashlib
import math
import secrets
from datetime import datetime, timedelta

from flask import current_app, request, session
from werkzeug.exceptions import TooManyRequests

from backend.extensions import db
from backend.models.seguranca import SessaoUsuario, TentativaAcesso


def _agora():
    return datetime.now().replace(microsecond=0)


# ---------------------------------------------------------------- sessões
def _hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def _hash_atual():
    token = session.get("token")
    return _hash(token) if isinstance(token, str) and token else None


def abrir_sessao(id_usuario):
    """Cria a sessão no banco e grava o token no cookie (substitui o anterior)."""
    agora = _agora()
    SessaoUsuario.query.filter(SessaoUsuario.id_usuario == id_usuario,
                               SessaoUsuario.expira_em <= agora).delete()
    token = secrets.token_urlsafe(32)
    db.session.add(SessaoUsuario(
        token_hash=_hash(token), id_usuario=id_usuario,
        expira_em=agora + current_app.config["PERMANENT_SESSION_LIFETIME"]))
    db.session.commit()
    session.clear()
    session["usuario_id"] = id_usuario
    session["token"] = token
    session.permanent = True


def sessao_valida(id_usuario):
    token_hash = _hash_atual()
    if token_hash is None:
        return False
    registro = db.session.get(SessaoUsuario, token_hash)
    return (registro is not None and registro.id_usuario == id_usuario
            and registro.expira_em > _agora())


def encerrar_sessao():
    token_hash = _hash_atual()
    if token_hash:
        SessaoUsuario.query.filter_by(token_hash=token_hash).delete()
        db.session.commit()
    session.clear()


def encerrar_outras_sessoes(id_usuario):
    """Após trocar senha/e-mail: derruba os outros aparelhos, mantém este."""
    consulta = SessaoUsuario.query.filter(SessaoUsuario.id_usuario == id_usuario)
    token_hash = _hash_atual()
    if token_hash:
        consulta = consulta.filter(SessaoUsuario.token_hash != token_hash)
    consulta.delete()


# ---------------------------------------------------- limite de tentativas
def ip_cliente():
    # Sem proxy reverso confiável, X-Forwarded-For pode ser forjado: usa o IP da conexão.
    return request.remote_addr or "desconhecido"


def chave_email(email):
    return "login:email:" + str(email).strip().lower()[:150]


def chave_ip(prefixo):
    return f"{prefixo}:ip:{ip_cliente()}"


def segundos_bloqueado(chave, maximo, janela):
    """0 se ainda pode tentar; senão, quantos segundos faltam para liberar."""
    inicio = _agora() - janela
    momentos = (db.session.query(TentativaAcesso.momento)
                .filter(TentativaAcesso.chave == chave, TentativaAcesso.momento > inicio)
                .order_by(TentativaAcesso.momento.desc()).limit(maximo).all())
    if len(momentos) < maximo:
        return 0
    liberacao = momentos[-1][0] + janela
    return max(1, math.ceil((liberacao - _agora()).total_seconds()))


def exigir_liberado(regras):
    """regras: [(chave, maximo, janela)]. Lança 429 com Retry-After."""
    espera = max((segundos_bloqueado(*regra) for regra in regras), default=0)
    if espera:
        raise TooManyRequests(
            description="Muitas tentativas. Aguarde alguns minutos e tente novamente.",
            retry_after=espera)


def registrar(*chaves):
    agora = _agora()
    # Limpeza barata: nenhuma regra usa janela maior que 1 dia.
    TentativaAcesso.query.filter(TentativaAcesso.momento < agora - timedelta(days=1)).delete()
    db.session.add_all(TentativaAcesso(chave=c, momento=agora) for c in chaves)
    db.session.commit()


def limpar(chave):
    TentativaAcesso.query.filter_by(chave=chave).delete()
    db.session.commit()


def regras_login(email):
    cfg = current_app.config
    janela = timedelta(minutes=cfg["LOGIN_JANELA_MINUTOS"])
    return [(chave_email(email), cfg["LOGIN_FALHAS_EMAIL"], janela),
            (chave_ip("login"), cfg["LOGIN_FALHAS_IP"], janela)]


def regras_cadastro():
    return [(chave_ip("cadastro"), current_app.config["CADASTROS_IP_HORA"], timedelta(hours=1))]
