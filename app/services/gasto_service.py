from app.repositories.gasto_repository import GastoRepository


class GastoService:

    def __init__(self):

        self.repository = GastoRepository()

    def listar(self):

        return self.repository.listar()

    def buscar_por_id(self, id_gasto):

        return self.repository.buscar_por_id(id_gasto)

    def inserir(self, gasto):

        self.repository.inserir(gasto)

    def atualizar(self, gasto):

        self.repository.atualizar(gasto)

    def excluir(self, id_gasto):

        self.repository.excluir(id_gasto)

    def gastos_por_categoria(self, id_usuario):

        return self.repository.gastos_por_categoria(id_usuario)
    
    def gastos_por_periodo(
        self, id_usuario, data_inicio, data_fim
    ):
        return self.repository.gastos_por_periodo(id_usuario, data_inicio,data_fim)
    
    def verificar_limite(self, id_usuario):
        return self.repository.verificar_limite(id_usuario)