from app.database import get_connection


class BoletoRepository:

    def listar(self):

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("select * from boleto order by vencimento")

        boletos = cursor.fetchall()

        cursor.close()
        conn.close()

        return boletos

    def buscar_por_id(self, id_boleto):

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "select * from boleto where id_boleto = %s",
            (id_boleto,)
        )

        boleto = cursor.fetchone()

        cursor.close()
        conn.close()

        return boleto

    def inserir(self, boleto):

        conn = get_connection()
        cursor = conn.cursor()

        sql = """
        insert into boleto
        (
            id_usuario,
            codigo_barras,
            valor,
            vencimento,
            status
        )
        values (%s, %s, %s, %s, %s)
        """

        cursor.execute(sql, (
            boleto.id_usuario,
            boleto.codigo_barras,
            boleto.valor,
            boleto.vencimento,
            boleto.status
        ))

        conn.commit()

        cursor.close()
        conn.close()

    def atualizar(self, boleto):

        conn = get_connection()
        cursor = conn.cursor()

        sql = """
        update boleto
        set
            id_usuario = %s,
            codigo_barras = %s,
            valor = %s,
            vencimento = %s,
            status = %s
        where id_boleto = %s
        """

        cursor.execute(sql, (
            boleto.id_usuario,
            boleto.codigo_barras,
            boleto.valor,
            boleto.vencimento,
            boleto.status,
            boleto.id_boleto
        ))

        conn.commit()

        cursor.close()
        conn.close()

    def excluir(self, id_boleto):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "delete from boleto where id_boleto = %s",
            (id_boleto,)
        )

        conn.commit()

        cursor.close()
        conn.close()

    def proximos_vencimentos(self, id_usuario):

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.callproc(
            "sp_boletos_proximos_vencimento",
            [id_usuario]
        )

        resultado = []

        for result in cursor.stored_results():

            resultado.extend(
                result.fetchall()
            )

        cursor.close()
        conn.close()

        return resultado