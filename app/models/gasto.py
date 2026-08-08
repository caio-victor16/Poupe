class Gasto:

    def __init__(
        self,
        id_gasto=None,
        id_usuario=None,
        id_categoria=None,
        valor=None,
        data=None,
        descricao=None,
        recorrente=False,
        tipo_pagamento=None,
        status_gasto=None
    ):
        self.id_gasto = id_gasto
        self.id_usuario = id_usuario
        self.id_categoria = id_categoria
        self.valor = valor
        self.data = data
        self.descricao = descricao
        self.recorrente = recorrente
        self.tipo_pagamento = tipo_pagamento
        self.status_gasto = status_gasto