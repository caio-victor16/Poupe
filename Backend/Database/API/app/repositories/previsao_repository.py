from app.database import get_raw_connection


class PrevisaoRepository:

    def calcular(self, id_usuario):

        conn = get_raw_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.callproc("sp_previsao_financeira", [id_usuario])

        resultado = []
        for result in cursor.stored_results():
            resultado.extend(result.fetchall())

        cursor.close()
        conn.close()

        return resultado[0] if resultado else None
