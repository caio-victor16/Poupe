from app.repositories.categoria_repository import CategoriaRepository


class CategoriaService:

    def __init__(self):
        self.repository = CategoriaRepository()

    def listar(self):
        return [c.to_dict() for c in self.repository.listar()]

    def buscar_por_id(self, id_categoria):
        categoria = self.repository.buscar_por_id(id_categoria)
        return categoria.to_dict() if categoria else None

    def inserir(self, categoria):
        self.repository.inserir(categoria)

    def atualizar(self, categoria):
        self.repository.atualizar(categoria)

    def excluir(self, id_categoria):
        self.repository.excluir(id_categoria)
