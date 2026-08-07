from app.database import get_connection

class GastoRepository:

    def gastos_por_categoria(self, id_usuario):

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.callproc(
            "sp_gastos_categoria",
            [id_usuario]
        )

        resultado = []

        for r in cursor.stored_results():
            resultado.extend(r.fetchall())

        cursor.close()
        conn.close()

        return resultado