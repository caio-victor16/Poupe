class Boleto:

    def __init__(
        self,
        id_boleto=None,
        id_usuario=None,
        codigo_barras=None,
        valor=None,
        vencimento=None,
        status=None
    ):
        self.id_boleto = id_boleto
        self.id_usuario = id_usuario
        self.codigo_barras = codigo_barras
        self.valor = valor
        self.vencimento = vencimento
        self.status = status