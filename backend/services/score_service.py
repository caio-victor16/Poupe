from backend.repositories.score_repository import ScoreRepository


class ScoreService:
    def __init__(self):
        self.repository = ScoreRepository()

    def calcular(self, id_usuario):
        dados = self.repository.indicadores(id_usuario)
        if dados is None:
            return None

        renda = float(dados["renda_mensal"])
        limite = float(dados["limite_gastos"])
        gasto = float(dados["gasto_mes"])
        atrasados = int(dados["boletos_atrasados"])
        na_semana = int(dados["boletos_na_semana"])

        pontos = 100
        dicas = []

        uso_limite = gasto / limite if limite else 0
        if uso_limite >= 1:
            pontos -= 35
            dicas.append("Você ultrapassou seu limite de gastos deste mês.")
        elif uso_limite >= 0.8:
            pontos -= 15
            dicas.append("Você já usou mais de 80% do limite. Segure os gastos não essenciais.")

        comprometimento = gasto / renda if renda else 0
        if comprometimento >= 0.9:
            pontos -= 25
            dicas.append("Seus gastos consomem quase toda a sua renda.")
        elif comprometimento >= 0.7:
            pontos -= 10
            dicas.append("Mais de 70% da renda está comprometida com gastos.")

        if atrasados:
            pontos -= min(atrasados * 10, 30)
            dicas.append(f"Você tem {atrasados} boleto(s) em atraso. Regularize para evitar juros.")

        if na_semana:
            pontos -= 5
            dicas.append(f"{na_semana} boleto(s) vencem nos próximos 7 dias.")

        pontos = max(pontos, 0)

        if pontos >= 80:
            classificacao = "excelente"
        elif pontos >= 60:
            classificacao = "boa"
        elif pontos >= 40:
            classificacao = "atencao"
        else:
            classificacao = "critica"

        if not dicas:
            dicas.append("Suas finanças estão em dia. Continue assim!")

        return {
            "id_usuario": id_usuario,
            "score": pontos,
            "classificacao": classificacao,
            "gasto_mes": gasto,
            "percentual_do_limite": round(uso_limite * 100, 1),
            "percentual_da_renda": round(comprometimento * 100, 1),
            "boletos_atrasados": atrasados,
            "dicas": dicas,
        }