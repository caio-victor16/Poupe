from datetime import date, timedelta
from backend.repositories.caixa_repository import CaixaRepository

class CaixaService:
    def __init__(self):
        self.repository = CaixaRepository()

    def calcular(self, id_usuario, saldo_atual):
        dados = self.repository.calcular(id_usuario)
        if dados is None:
            return None

        media_diaria = float(dados["media_diaria"])
        boletos = float(dados["boletos_30_dias"])
        saldo_livre = saldo_atual - boletos

        dias_de_folego = None
        data_caixa_zerado = None

        if media_diaria > 0:
            dias_de_folego = max(int(saldo_livre // media_diaria), 0)
            if dias_de_folego <= 365:
                data_caixa_zerado = (date.today() + timedelta(days=dias_de_folego)).isoformat()

        if saldo_livre < 0:
            situacao = "negativo"
        elif dias_de_folego is not None and dias_de_folego < 30:
            situacao = "apertado"
        else:
            situacao = "tranquilo"

        return {
            "saldo_atual": saldo_atual,
            "boletos_30_dias": boletos,
            "saldo_apos_boletos": round(saldo_livre, 2),
            "media_gasto_diario": round(media_diaria, 2),
            "gasto_diario_seguro": round(max(saldo_livre, 0) / 30, 2),
            "dias_de_folego": dias_de_folego,
            "data_caixa_zerado": data_caixa_zerado,
            "situacao": situacao,
        }