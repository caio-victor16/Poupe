from app.repositories.alerta_repository import AlertaRepository


class AlertaService:

    def __init__(self):

        self.repository = AlertaRepository()

    def listar_por_usuario(self, id_usuario):

        return self.repository.listar_por_usuario(
            id_usuario
        )

    def buscar_por_id(self, id_alert):

        return self.repository.buscar_por_id(
            id_alert
        )

    def inserir(self, alerta):

        self.repository.inserir(alerta)

    def marcar_como_visualizado(self, id_alert):

        self.repository.marcar_como_visualizado(
            id_alert
        )

    def excluir(self, id_alert):

        self.repository.excluir(id_alert)

    def gerar_alerta_limite(self, id_usuario):

        self.repository.gerar_alerta_limite(id_usuario)