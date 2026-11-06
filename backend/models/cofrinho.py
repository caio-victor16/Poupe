from backend.extensions import db


class Cofrinho(db.Model):
    """Cofrinho com prazo da tela cofrinho.html (aportes somam em valor_guardado)."""
    __tablename__ = "cofrinho"

    id_cofrinho = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    valor_alvo = db.Column(db.Numeric(10, 2), nullable=False)
    valor_guardado = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    prazo_meses = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {"id_cofrinho": self.id_cofrinho, "id_usuario": self.id_usuario,
                "titulo": self.titulo, "valor_alvo": float(self.valor_alvo),
                "valor_guardado": float(self.valor_guardado), "prazo_meses": self.prazo_meses}
