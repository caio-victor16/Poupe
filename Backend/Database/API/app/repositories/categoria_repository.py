from app.models.categoria import Categoria


class CategoriaRepository:
    def listar(self):
        return Categoria.listar_todos()

    def buscar_por_id(self, id_categoria):
        return Categoria.buscar_por_id(id_categoria)

    def inserir(self, categoria):
        categoria.salvar()

    def atualizar(self, categoria, dados):
        categoria.atualizar(nome=dados.get("nome"))

    def excluir(self, categoria):
        categoria.deletar()
