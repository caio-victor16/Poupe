from backend.models.categoria import Categoria


class CategoriaService:
    def listar(self):
        return [c.to_dict() for c in Categoria.listar_todos()]

    def buscar_por_id(self, id_categoria):
        categoria = Categoria.buscar_por_id(id_categoria)
        return categoria.to_dict() if categoria else None

    def criar(self, dados):
        if not dados.get("nome"):
            raise ValueError("O campo 'nome' é obrigatório.")
        categoria = Categoria(nome=dados["nome"])
        categoria.salvar()
        return categoria.to_dict()

    def atualizar(self, id_categoria, dados):
        categoria = Categoria.buscar_por_id(id_categoria)
        if categoria is None:
            return None
        categoria.atualizar(nome=dados.get("nome"))
        return categoria.to_dict()

    def excluir(self, id_categoria):
        categoria = Categoria.buscar_por_id(id_categoria)
        if categoria is None:
            return False
        categoria.deletar()
        return True
