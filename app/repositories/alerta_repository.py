from app.database import get_connection


class AlertaRepository:

    def listar_por_usuario(self, id_usuario):

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            select *
            from alerta
            where id_usuario = %s
            order by data desc
            """,
            (id_usuario,)
        )

        alertas = cursor.fetchall()

        cursor.close()
        conn.close()

        return alertas

    def buscar_por_id(self, id_alert):

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            select *
            from alerta
            where id_alert = %s
            """,
            (id_alert,)
        )

        alerta = cursor.fetchone()

        cursor.close()
        conn.close()

        return alerta

    def inserir(self, alerta):

        conn = get_connection()
        cursor = conn.cursor()

        sql = """
        insert into alerta
        (
            id_usuario,
            tipo,
            mensagem,
            data,
            visualizado
        )
        values (%s, %s, %s, %s, %s)
        """

        cursor.execute(
            sql,
            (
                alerta.id_usuario,
                alerta.tipo,
                alerta.mensagem,
                alerta.data,
                alerta.visualizado
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

    def marcar_como_visualizado(self, id_alert):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            update alerta
            set visualizado = true
            where id_alert = %s
            """,
            (id_alert,)
        )

        conn.commit()

        cursor.close()
        conn.close()

    def excluir(self, id_alert):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            delete from alerta
            where id_alert = %s
            """,
            (id_alert,)
        )

        conn.commit()

        cursor.close()
        conn.close()

    def gerar_alerta_limite(self, id_usuario):

        conn = get_connection()

        cursor = conn.cursor()

        cursor.callproc(
            "sp_gerar_alerta_limite",
            [id_usuario]
        )

        conn.commit()

        cursor.close()
        conn.close()