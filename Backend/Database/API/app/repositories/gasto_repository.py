from app.database import db, get_raw_connection
from app.models.gasto import Gasto


class GastoRepository:

    def listar(self):
        return Gasto.query.all()

    def buscar_por_id(self, id_gasto):
        return Gasto.query.get(id_gasto)

    def inserir(self, gasto):
        db.session.add(gasto)
        db.session.commit()

    def atualizar(self, gasto):

        existente = Gasto.query.get(gasto.id_gasto)

        if not existente:
            return

        existente.id_usuario = gasto.id_usuario
        existente.id_categoria = gasto.id_categoria
        existente.valor = gasto.valor
        existente.data = gasto.data
        existente.descricao = gasto.descricao
        existente.recorrente = gasto.recorrente
        existente.tipo_pagamento = gasto.tipo_pagamento
        existente.status_gasto = gasto.status_gasto

        db.session.commit()

    def excluir(self, id_gasto):

        gasto = Gasto.query.get(id_gasto)

        if gasto:
            db.session.delete(gasto)
            db.session.commit()

    def gastos_por_categoria(self, id_usuario):

        conn = get_raw_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.callproc("sp_gastos_categoria", [id_usuario])

        resultado = []
        for result in cursor.stored_results():
            resultado.extend(result.fetchall())

        cursor.close()
        conn.close()

        return resultado

    def gastos_por_periodo(self, id_usuario, data_inicio, data_fim):

        conn = get_raw_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.callproc(
            "sp_gastos_por_periodo",
            [id_usuario, data_inicio, data_fim]
        )

        resultado = []
        for result in cursor.stored_results():
            resultado.extend(result.fetchall())

        cursor.close()
        conn.close()

        return resultado

    def verificar_limite(self, id_usuario):

        conn = get_raw_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.callproc("sp_verificar_limite_gastos", [id_usuario])

        resultado = []
        for result in cursor.stored_results():
            resultado.extend(result.fetchall())

        cursor.close()
        conn.close()

        return resultado[0] if resultado else None
