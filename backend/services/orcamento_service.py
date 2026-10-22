from backend.extensions import db
from backend.models.alerta import Alerta
from backend.models.orcamento_categoria import OrcamentoCategoria
from backend.repositories.orcamento_repository import OrcamentoRepository


class OrcamentoService:
    def __init__(self):
        self.repository = OrcamentoRepository()

    @staticmethod
    def _classificar(percentual):
        if percentual >= 100:
            return "estourado"
        if percentual >= 80:
            return "atencao"
        return "ok"

    def definir(self, dados):
        for campo in ["id_usuario", "id_categoria", "limite"]:
            if dados.get(campo) in (None, ""):
                raise ValueError(f"O campo '{campo}' é obrigatório.")

        try:
            limite = float(dados["limite"])
        except (TypeError, ValueError):
            raise ValueError("O campo 'limite' deve ser numérico.")
        if limite <= 0:
            raise ValueError("O limite deve ser maior que zero.")

        existente = OrcamentoCategoria.buscar_por_usuario_e_categoria(
            dados["id_usuario"], dados["id_categoria"]
        )
        if existente:
            existente.atualizar_limite(limite)
            return existente.to_dict()

        orcamento = OrcamentoCategoria(
            id_usuario=dados["id_usuario"],
            id_categoria=dados["id_categoria"],
            limite=limite,
        )
        orcamento.salvar()
        return orcamento.to_dict()

    def status_do_mes(self, id_usuario):
        itens = []
        for linha in self.repository.status_do_mes(id_usuario):
            limite = float(linha["limite"])
            gasto = float(linha["gasto_mes"])
            percentual = round(gasto / limite * 100, 2) if limite else 0
            itens.append({
                "id_orcamento": linha["id_orcamento"],
                "id_categoria": linha["id_categoria"],
                "categoria": linha["categoria"],
                "limite": limite,
                "gasto_mes": gasto,
                "restante": round(limite - gasto, 2),
                "percentual": percentual,
                "situacao": self._classificar(percentual),
            })
        return itens

    def gerar_alertas(self, id_usuario):
        """Cria um alerta por categoria em risco, no máximo um por dia."""
        criados = 0
        for item in self.status_do_mes(id_usuario):
            if item["situacao"] == "ok":
                continue

            if item["situacao"] == "estourado":
                mensagem = f"O orçamento de {item['categoria']} foi ultrapassado."
            else:
                mensagem = f"O orçamento de {item['categoria']} está próximo do limite."

            ja_existe = Alerta.query.filter(
                Alerta.id_usuario == id_usuario,
                Alerta.tipo == "orcamento",
                Alerta.mensagem == mensagem,
                db.func.date(Alerta.data) == db.func.curdate(),
            ).first()
            if ja_existe:
                continue

            Alerta(
                id_usuario=id_usuario, tipo="orcamento", mensagem=mensagem
            ).salvar()
            criados += 1
        return criados

    def excluir(self, id_orcamento):
        orcamento = OrcamentoCategoria.buscar_por_id(id_orcamento)
        if orcamento is None:
            return False
        orcamento.deletar()
        return True