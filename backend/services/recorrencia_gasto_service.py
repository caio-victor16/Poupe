import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from backend.extensions import db
from backend.models.gasto import Gasto
from backend.models.recorrencia_gasto import RecorrenciaGasto
from backend.repositories.recorrencia_gasto_repository import (
    RecorrenciaGastoRepository,
)


class RecorrenciaGastoService:
    FREQUENCIAS = {"semanal", "mensal", "anual"}

    def __init__(self):
        self.repository = RecorrenciaGastoRepository()

    @staticmethod
    def _parse_data(valor, campo):
        if isinstance(valor, datetime):
            return valor.date()
        if isinstance(valor, date):
            return valor
        if not isinstance(valor, str):
            raise ValueError(f"O campo '{campo}' deve estar no formato AAAA-MM-DD.")
        try:
            return date.fromisoformat(valor)
        except ValueError as erro:
            raise ValueError(
                f"O campo '{campo}' deve estar no formato AAAA-MM-DD."
            ) from erro

    @staticmethod
    def _parse_valor(valor):
        try:
            valor_decimal = Decimal(str(valor))
        except (InvalidOperation, TypeError, ValueError) as erro:
            raise ValueError("O campo 'valor' deve ser um número válido.") from erro
        if not valor_decimal.is_finite() or valor_decimal <= 0:
            raise ValueError("O campo 'valor' deve ser maior que zero.")
        return valor_decimal

    @staticmethod
    def _avancar_data(data_atual, frequencia, dia_mes):
        if frequencia == "semanal":
            return data_atual + timedelta(weeks=1)

        if frequencia == "mensal":
            ano = data_atual.year + (data_atual.month == 12)
            mes = data_atual.month % 12 + 1
            dia = min(dia_mes, calendar.monthrange(ano, mes)[1])
            return date(ano, mes, dia)

        ano = data_atual.year + 1
        dia = min(dia_mes, calendar.monthrange(ano, data_atual.month)[1])
        return date(ano, data_atual.month, dia)

    def listar_por_usuario(self, id_usuario):
        return [
            recorrencia.to_dict()
            for recorrencia in self.repository.listar_por_usuario(id_usuario)
        ]

    def buscar_por_id(self, id_recorrencia):
        recorrencia = self.repository.buscar_por_id(id_recorrencia)
        return recorrencia.to_dict() if recorrencia else None

    def criar(self, dados):
        if not isinstance(dados, dict):
            raise ValueError("O corpo da requisição deve ser um objeto JSON.")
        obrigatorios = [
            "id_usuario", "id_categoria", "valor", "frequencia", "proxima_data"
        ]
        for campo in obrigatorios:
            if dados.get(campo) is None:
                raise ValueError(f"O campo '{campo}' é obrigatório.")

        frequencia = dados["frequencia"]
        if frequencia not in self.FREQUENCIAS:
            raise ValueError("A frequência deve ser semanal, mensal ou anual.")

        proxima_data = self._parse_data(dados["proxima_data"], "proxima_data")
        recorrencia = RecorrenciaGasto(
            id_usuario=int(dados["id_usuario"]),
            id_categoria=int(dados["id_categoria"]),
            valor=self._parse_valor(dados["valor"]),
            descricao=dados.get("descricao"),
            frequencia=frequencia,
            proxima_data=proxima_data,
            dia_mes=proxima_data.day,
            tipo_pagamento=dados.get("tipo_pagamento"),
            ativa=True,
        )
        self.repository.salvar(recorrencia)
        return recorrencia.to_dict()

    def atualizar(self, id_recorrencia, dados):
        if not isinstance(dados, dict):
            raise ValueError("O corpo da requisição deve ser um objeto JSON.")
        recorrencia = self.repository.buscar_por_id(id_recorrencia)
        if recorrencia is None:
            return None

        if "id_categoria" in dados:
            recorrencia.id_categoria = int(dados["id_categoria"])
        if "valor" in dados:
            recorrencia.valor = self._parse_valor(dados["valor"])
        if "descricao" in dados:
            recorrencia.descricao = dados["descricao"]
        if "frequencia" in dados:
            if dados["frequencia"] not in self.FREQUENCIAS:
                raise ValueError("A frequência deve ser semanal, mensal ou anual.")
            recorrencia.frequencia = dados["frequencia"]
        if "proxima_data" in dados:
            recorrencia.proxima_data = self._parse_data(
                dados["proxima_data"], "proxima_data"
            )
            recorrencia.dia_mes = recorrencia.proxima_data.day
        if "tipo_pagamento" in dados:
            recorrencia.tipo_pagamento = dados["tipo_pagamento"]
        if "ativa" in dados:
            if not isinstance(dados["ativa"], bool):
                raise ValueError("O campo 'ativa' deve ser verdadeiro ou falso.")
            recorrencia.ativa = dados["ativa"]

        self.repository.salvar(recorrencia)
        return recorrencia.to_dict()

    def excluir(self, id_recorrencia):
        recorrencia = self.repository.buscar_por_id(id_recorrencia)
        if recorrencia is None:
            return False
        self.repository.excluir(recorrencia)
        return True

    def processar_vencidas(self, id_usuario, hoje=None):
        hoje = hoje or date.today()
        recorrencias = self.repository.listar_vencidas(id_usuario, hoje)
        gastos_gerados = []

        for recorrencia in recorrencias:
            while recorrencia.proxima_data <= hoje:
                gasto = Gasto(
                    id_usuario=recorrencia.id_usuario,
                    id_categoria=recorrencia.id_categoria,
                    valor=recorrencia.valor,
                    data=recorrencia.proxima_data,
                    descricao=recorrencia.descricao,
                    recorrente=True,
                    tipo_pagamento=recorrencia.tipo_pagamento,
                )
                db.session.add(gasto)
                gastos_gerados.append(gasto)
                recorrencia.proxima_data = self._avancar_data(
                    recorrencia.proxima_data,
                    recorrencia.frequencia,
                    recorrencia.dia_mes,
                )

        db.session.commit()
        return [gasto.to_dict() for gasto in gastos_gerados]