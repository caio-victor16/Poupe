from backend.extensions import db


class OrcamentoCategoria(db.Model):
    __tablename__ = "orcamento_categoria"

    id_orcamento = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(
        db.Integer, db.ForeignKey("usuario.id_usuario"), nullable=False
    )
    id_categoria = db.Column(
        db.Integer, db.ForeignKey("categoria.id_categoria"), nullable=False
    )
    limite = db.Column(db.Numeric(10, 2), nullable=False)

    def salvar(self):
        db.session.add(self)
        db.session.commit()

    def deletar(self):
        db.session.delete(self)
        db.session.commit()

    def atualizar_limite(self, limite):
        self.limite = limite
        db.session.commit()

    @classmethod
    def buscar_por_id(cls, id_orcamento):
        return db.session.get(cls, id_orcamento)

    @classmethod
    def buscar_por_usuario_e_categoria(cls, id_usuario, id_categoria):
        return cls.query.filter_by(
            id_usuario=id_usuario, id_categoria=id_categoria
        ).first()

    def to_dict(self):
        return {
            "id_orcamento": self.id_orcamento,
            "id_usuario": self.id_usuario,
            "id_categoria": self.id_categoria,
            "limite": float(self.limite),
        }