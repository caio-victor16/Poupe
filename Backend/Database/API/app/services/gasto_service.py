from app.repositories.gasto_repository import GastoRepository

class GastoService:

    def __init__(self):
        self.repository = GastoRepository()

    def buscar_gastos_categoria(self, id_usuario):
        return self.repository.gastos_por_categoria(id_usuario)