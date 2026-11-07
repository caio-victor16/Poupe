from backend.extensions import db


class SessaoUsuario(db.Model):
    """Sessão aberta no login (REV-002). O cookie guarda só o token; o banco
    guarda o hash SHA-256. Apagar a linha encerra a sessão, mesmo que alguém
    tenha copiado o cookie."""
    __tablename__ = "sessao_usuario"

    token_hash = db.Column(db.String(64), primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
                           nullable=False, index=True)
    expira_em = db.Column(db.DateTime, nullable=False)


class TentativaAcesso(db.Model):
    """Uma linha por tentativa contada (REV-001): falhas de login/senha atual
    e cadastros, agrupados por chave (ex.: "login:email:x@y.com")."""
    __tablename__ = "tentativa_acesso"

    id_tentativa = db.Column(db.Integer, primary_key=True, autoincrement=True)
    chave = db.Column(db.String(190), nullable=False)
    momento = db.Column(db.DateTime, nullable=False, index=True)

    __table_args__ = (db.Index("idx_tentativa_chave_momento", "chave", "momento"),)


class RedefinicaoSenha(db.Model):
    """Link de "esqueci minha senha": vale 30 minutos e uma vez só. O e-mail leva
    o token; o banco guarda só o hash SHA-256."""
    __tablename__ = "redefinicao_senha"

    token_hash = db.Column(db.String(64), primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
                           nullable=False, index=True)
    expira_em = db.Column(db.DateTime, nullable=False)
