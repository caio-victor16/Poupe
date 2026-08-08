from app.database import get_connection


class PrevisaoRepository:

    def calcular(self, id_usuario):

        conn = get_connection()

        cursor = conn.cursor(dictionary=True)

        cursor.callproc(
            "sp_previsao_financeira",
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