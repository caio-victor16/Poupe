"""Recuperação de senha por e-mail ("Esqueceu sua senha?").

1. POST /senha/esqueci {email}: se a conta existir, envia um link que vale
   30 minutos. A resposta é sempre a mesma (não revela se o e-mail existe).
2. POST /senha/redefinir {token, senha}: troca a senha, invalida o link e
   encerra todas as sessões abertas da conta.
"""
import hashlib
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from backend import seguranca
from backend.extensions import db
from backend.models.seguranca import RedefinicaoSenha, SessaoUsuario
from backend.models.usuario import Usuario
from backend.passwords import gerar_hash, validar_senha
from backend.services.email_service import enviar_email, smtp_configurado

VALIDADE = timedelta(minutes=30)
MENSAGEM_ENVIADA = ("Se este e-mail estiver cadastrado, enviamos um link para criar uma "
                    "nova senha. Ele vale por 30 minutos. Confira também a caixa de spam.")
LINK_INVALIDO = "Link inválido ou expirado. Peça um novo em \"Esqueceu sua senha?\"."

senha_bp = Blueprint("senha", __name__)


def _hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def _agora():
    return datetime.now().replace(microsecond=0)


def _corpo():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        raise ValueError("Informe um objeto JSON.")
    return dados


@senha_bp.route("/senha/esqueci", methods=["POST"])
def esqueci():
    try:
        email = _corpo().get("email")
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    if not isinstance(email, str) or "@" not in email or len(email) > 150:
        return jsonify({"erro": "Informe um e-mail válido."}), 400
    email = email.strip()

    cfg = current_app.config
    if not smtp_configurado() and not cfg["DEBUG"]:
        return jsonify({"erro": "Recuperação de senha não está configurada no servidor."}), 503

    # Limite por e-mail e por IP: evita usar a rota para lotar a caixa de alguém.
    chave_email = "senha:email:" + email.lower()
    seguranca.exigir_liberado([
        (chave_email, cfg["SENHA_PEDIDOS_EMAIL_HORA"], timedelta(hours=1)),
        (seguranca.chave_ip("senha"), cfg["SENHA_PEDIDOS_IP_HORA"], timedelta(hours=1)),
    ])
    seguranca.registrar(chave_email, seguranca.chave_ip("senha"))

    try:
        usuario = Usuario.buscar_por_email(email)
        if usuario is not None:
            # Um link por vez: pedir de novo invalida o anterior.
            RedefinicaoSenha.query.filter_by(id_usuario=usuario.id_usuario).delete()
            token = secrets.token_urlsafe(32)
            db.session.add(RedefinicaoSenha(token_hash=_hash(token), id_usuario=usuario.id_usuario,
                                            expira_em=_agora() + VALIDADE))
            db.session.commit()
            # Endereço do .env (APP_URL), nunca do cabeçalho Host da requisição:
            # senão um atacante faria o e-mail apontar para o site dele.
            # O token vai depois do "#": o navegador não o envia ao servidor nem a logs.
            link = f"{cfg['APP_URL'].rstrip('/')}/redefinir-senha.html#token={token}"
            texto = (f"Olá, {usuario.nome.split()[0]}!\n\n"
                     "Recebemos um pedido para criar uma nova senha no Poupe+.\n"
                     f"Abra o link abaixo em até 30 minutos:\n\n{link}\n\n"
                     "Se não foi você, ignore este e-mail: sua senha continua a mesma.\n")
            if smtp_configurado():
                enviar_email(usuario.email, "Poupe+: criar uma nova senha", texto)
            else:
                # Só com POUPE_DEBUG=true e sem SMTP: mostra o link no terminal para testes.
                current_app.logger.warning("Modo desenvolvimento, sem SMTP. Link de nova senha: %s", link)
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Não foi possível processar o pedido. Tente novamente."}), 500
    return jsonify({"mensagem": MENSAGEM_ENVIADA}), 200


@senha_bp.route("/senha/redefinir", methods=["POST"])
def redefinir():
    try:
        dados = _corpo()
        senha = dados.get("senha")
        validar_senha(senha)
    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400
    token = dados.get("token")
    if not isinstance(token, str) or not 20 <= len(token) <= 100:
        return jsonify({"erro": LINK_INVALIDO}), 400

    pedido = db.session.get(RedefinicaoSenha, _hash(token))
    if pedido is None or pedido.expira_em <= _agora():
        return jsonify({"erro": LINK_INVALIDO}), 400
    usuario = db.session.get(Usuario, pedido.id_usuario)
    if usuario is None:
        return jsonify({"erro": LINK_INVALIDO}), 400

    usuario.senha = gerar_hash(senha)
    RedefinicaoSenha.query.filter_by(id_usuario=usuario.id_usuario).delete()
    # Quem tinha a sessão aberta (inclusive um invasor) precisa entrar de novo.
    SessaoUsuario.query.filter_by(id_usuario=usuario.id_usuario).delete()
    db.session.commit()
    # Libera o login caso o usuário tenha sido bloqueado por errar a senha antiga.
    seguranca.limpar(seguranca.chave_email(usuario.email))
    return jsonify({"mensagem": "Senha alterada! Entre com a nova senha."}), 200
