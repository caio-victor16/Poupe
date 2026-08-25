from backend.extensions import db


class Categoria(db.Model):
    __tablename__ = "categoria"

    id_categoria = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(60), nullable=False)

    def salvar(self):
        db.session.add(self)
        db.session.commit()

    def atualizar(self, nome=None):
        if nome is not None:
            self.nome = nome
        db.session.commit()

    def deletar(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def listar_todos():
        return Categoria.query.order_by(Categoria.nome.asc()).all()

    @staticmethod
    def buscar_por_id(id_categoria):
        return Categoria.query.get(id_categoria)

    def to_dict(self):
        return {
            "id_categoria": self.id_categoria,
            "nome": self.nome,
        }
