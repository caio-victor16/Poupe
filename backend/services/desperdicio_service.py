from backend.repositories.desperdicio_repository import DesperdicioRepository
class DesperdicioService:
    def __init__(self):
        self.repository = DesperdicioRepository()

    def analisar(self, id_usuario):
        categorias = self.repository.categorias_acima_da_media(id_usuario)
        assinaturas = self.repository.assinaturas_provaveis(id_usuario)
        duplicados = self.repository.gastos_duplicados(id_usuario)

        for gasto in duplicados:
            gasto["data"] = gasto["data"].isoformat()

        return {
            "categorias_acima_da_media": categorias,
            "assinaturas_provaveis": assinaturas,
            "gastos_duplicados": duplicados,
            "total_alertas": len(categorias) + len(assinaturas) + len(duplicados),
        }