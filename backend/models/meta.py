from backend.extensions import db


class Meta(db.Model):
    """Meta de economia da tela metas.html."""
    __tablename__ = "meta"

    id_meta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    valor_alvo = db.Column(db.Numeric(10, 2), nullable=False)
    valor_guardado = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    def to_dict(self):
        return {"id_meta": self.id_meta, "id_usuario": self.id_usuario, "titulo": self.titulo,
                "valor_alvo": float(self.valor_alvo), "valor_guardado": float(self.valor_guardado)}
