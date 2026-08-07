class Previsao:

    def __init__(
        self,
        id_previsao=None,
        id_usuario=None,
        valor_previsto=None,
        data_previsao=None,
        risco_endividamento=None,
        recomendacao=None
    ):
        self.id_previsao = id_previsao
        self.id_usuario = id_usuario
        self.valor_previsto = valor_previsto
        self.data_previsao = data_previsao
        self.risco_endividamento = risco_endividamento
        self.recomendacao = recomendacao