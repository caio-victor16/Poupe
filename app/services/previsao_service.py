from app.repositories.previsao_repository import PrevisaoRepository


class PrevisaoService:

    def __init__(self):

        self.repository = PrevisaoRepository()

    def calcular(self, id_usuario):

        return self.repository.calcular(
            id_usuario
        )