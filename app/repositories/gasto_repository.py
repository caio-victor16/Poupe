from app.database import get_connection

class GastoRepository:

    def listar(self):

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("select * from gasto")

        gastos = cursor.fetchall()

        cursor.close()
        conn.close()

        return gastos

    def buscar_por_id(self, id_gasto):

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "select * from gasto where id_gasto = %s",
            (id_gasto,)
        )

        gasto = cursor.fetchone()

        cursor.close()
        conn.close()

        return gasto

    def inserir(self, gasto):

        conn = get_connection()
        cursor = conn.cursor()

        sql = """
        insert into gasto
        (
            id_usuario,
            id_categoria,
            valor,
            data,
            descricao,
            recorrente,
            tipo_pagamento,
            status_gasto
        )
        values (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(sql, (
            gasto.id_usuario,
            gasto.id_categoria,
            gasto.valor,
            gasto.data,
            gasto.descricao,
            gasto.recorrente,
            gasto.tipo_pagamento,
            gasto.status_gasto
        ))

        conn.commit()

        cursor.close()
        conn.close()

    def atualizar(self, gasto):

        conn = get_connection()
        cursor = conn.cursor()

        sql = """
        update gasto
        set
            id_usuario = %s,
            id_categoria = %s,
            valor = %s,
            data = %s,
            descricao = %s,
            recorrente = %s,
            tipo_pagamento = %s,
            status_gasto = %s
        where id_gasto = %s
        """

        cursor.execute(sql, (
            gasto.id_usuario,
            gasto.id_categoria,
            gasto.valor,
            gasto.data,
            gasto.descricao,
            gasto.recorrente,
            gasto.tipo_pagamento,
            gasto.status_gasto,
            gasto.id_gasto
        ))

        conn.commit()

        cursor.close()
        conn.close()

    def excluir(self, id_gasto):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "delete from gasto where id_gasto = %s",
            (id_gasto,)
        )

        conn.commit()

        cursor.close()
        conn.close()

    def gastos_por_categoria(self, id_usuario):

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.callproc(
            "sp_gastos_categoria",
            [id_usuario]
        )

        resultado = []

        for result in cursor.stored_results():
            resultado.extend(result.fetchall())

        cursor.close()
        conn.close()

        return resultado
    
    def gastos_por_periodo(
        self,
        id_usuario,
        data_inicio,
        data_fim
    ):

        conn = get_connection()

        cursor = conn.cursor(dictionary=True)

        cursor.callproc(
            "sp_gastos_por_periodo",
            [
                id_usuario,
                data_inicio,
                data_fim
            ]
        )

        resultado = []

        for result in cursor.stored_results():

            resultado.extend(
                result.fetchall()
            )

        cursor.close()
        conn.close()

        return resultado
    
    def verificar_limite(self, id_usuario):

        conn = get_connection()

        cursor = conn.cursor(dictionary=True)

        cursor.callproc(
            "sp_verificar_limite_gastos",
            [id_usuario]
        )

        resultado = []

        for result in cursor.stored_results():

            resultado.extend(
                result.fetchall()
            )

        cursor.close()
        conn.close()

        if resultado:

            return resultado[0]

        return None