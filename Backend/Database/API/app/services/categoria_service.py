from app.repositories.categoria_repository import CategoriaRepository


class CategoriaService:

    def __init__(self):

        self.repository = CategoriaRepository()

    def listar(self):

        return self.repository.listar()

    def buscar_por_id(self, id_categoria):

        return self.repository.buscar_por_id(id_categoria)

    def inserir(self, categoria):

        self.repository.inserir(categoria)

    def atualizar(self, categoria):

        self.repository.atualizar(categoria)

    def excluir(self, id_categoria):

        self.repository.excluir(id_categoria)