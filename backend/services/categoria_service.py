from backend.repositories.categoria_repository import CategoriaRepository
from backend.models.categoria import Categoria


class CategoriaService:
    def __init__(self):
        self.repository = CategoriaRepository()

    def listar(self):
        return [c.to_dict() for c in self.repository.listar()]

    def buscar_por_id(self, id_categoria):
        categoria = self.repository.buscar_por_id(id_categoria)
        return categoria.to_dict() if categoria else None

    def criar(self, dados):
        if not dados.get("nome"):
            raise ValueError("O campo 'nome' é obrigatório.")

        categoria = Categoria(nome=dados["nome"])
        self.repository.inserir(categoria)
        return categoria.to_dict()

    def atualizar(self, id_categoria, dados):
        categoria = self.repository.buscar_por_id(id_categoria)
        if categoria is None:
            return None

        self.repository.atualizar(categoria, dados)
        return categoria.to_dict()

    def excluir(self, id_categoria):
        categoria = self.repository.buscar_por_id(id_categoria)
        if categoria is None:
            return False

        self.repository.excluir(categoria)
        return True
