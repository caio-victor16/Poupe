class Alerta:

    def __init__(
        self,
        id_alerta=None,
        id_usuario=None,
        tipo=None,
        mensagem=None,
        data=None,
        visualizado=False
    ):
        self.id_alerta = id_alerta
        self.id_usuario = id_usuario
        self.tipo = tipo
        self.mensagem = mensagem
        self.data = data
        self.visualizado = visualizado