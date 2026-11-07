"""Regras da aba Boletos: cadastrar, pagar (vira gasto), desfazer pagamento,
débito automático e avisos de vencimento."""
import calendar
import re
from datetime import date
from decimal import Decimal

from sqlalchemy import update

from backend.crud import booleano, data_iso, dinheiro, id_existente, texto, validar_campos
from backend.extensions import db
from backend.models.alerta import Alerta
from backend.models.boleto import Boleto
from backend.models.categoria import Categoria
from backend.models.gasto import Gasto
from backend.repositories.boleto_repository import BoletoRepository


def codigo_barras(valor, campo):
    """Opcional. Código de barras (44) ou linha digitável (47/48); aceita espaços,
    pontos e hífens e grava só os dígitos. Vazio vira None."""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return None
    if not isinstance(valor, str) or not re.fullmatch(r"[0-9 .\-]+", valor.strip()):
        raise ValueError(f"O campo '{campo}' deve conter só números (espaços, pontos e hífens são ignorados).")
    digitos = re.sub(r"\D", "", valor)
    if not 44 <= len(digitos) <= 48:
        raise ValueError(f"O campo '{campo}' deve ter de 44 a 48 dígitos.")
    return digitos


CAMPOS_OBRIGATORIOS = {
    "descricao": texto(100),
    "valor": dinheiro(Decimal("0"), incluir_minimo=False),
    "vencimento": data_iso,
    "id_categoria": id_existente(Categoria, "categoria"),
}
CAMPOS_OPCIONAIS = {
    "codigo_barras": codigo_barras,
    "fixo": booleano,
    "debito_automatico": booleano,
}
MAX_MESES_ATRASADOS = 36   # débito automático: no máximo 3 anos de uma vez
DIAS_AVISO = 3


def proximo_vencimento(vencimento, dia):
    """Mesmo dia no mês seguinte; 31 vira 30/29/28 quando o mês é menor."""
    ano, mes = (vencimento.year + 1, 1) if vencimento.month == 12 else (vencimento.year, vencimento.month + 1)
    return date(ano, mes, min(dia or vencimento.day, calendar.monthrange(ano, mes)[1]))


def brl(valor):
    return "R$ " + f"{Decimal(valor):,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


class BoletoService:
    def __init__(self):
        self.repository = BoletoRepository()

    def listar(self):
        return [b.to_dict() for b in Boleto.listar_todos()]

    def listar_por_usuario(self, id_usuario):
        return [b.to_dict() for b in Boleto.listar_por_usuario(id_usuario)]

    def buscar_por_id(self, id_boleto):
        boleto = Boleto.buscar_por_id(id_boleto)
        return boleto.to_dict() if boleto else None

    def criar(self, dados):
        limpos = validar_campos(CAMPOS_OBRIGATORIOS, dados)
        limpos.update(validar_campos(CAMPOS_OPCIONAIS, dados, parcial=True))
        if dados.get("id_usuario") is None:
            raise ValueError("O campo 'id_usuario' é obrigatório.")
        boleto = Boleto(id_usuario=dados["id_usuario"], status="pendente",
                        dia_vencimento=limpos["vencimento"].day, **limpos)
        boleto.salvar()
        return boleto.to_dict()

    def atualizar(self, id_boleto, dados):
        boleto = Boleto.buscar_por_id(id_boleto)
        if boleto is None:
            return None
        # "status" não se altera aqui: pagar/desfazer têm rotas próprias (criam/apagam o gasto).
        limpos = validar_campos({**CAMPOS_OBRIGATORIOS, **CAMPOS_OPCIONAIS}, dados, parcial=True)
        for campo, valor in limpos.items():
            setattr(boleto, campo, valor)
        if "vencimento" in limpos:
            boleto.dia_vencimento = limpos["vencimento"].day
        db.session.commit()
        return boleto.to_dict()

    def excluir(self, id_boleto):
        boleto = Boleto.buscar_por_id(id_boleto)
        if boleto is None:
            return False
        boleto.deletar()   # o gasto de um boleto pago continua em Gastos
        return True

    # ---- pagamento -------------------------------------------------------
    def _pagar(self, boleto, data_pagamento, valor, automatico=False):
        if boleto.id_categoria is None:
            raise ValueError("Escolha uma categoria para o boleto antes de pagar.")
        # Marca como pago só se ainda não estiver (dois cliques não geram dois gastos).
        marcado = db.session.execute(
            update(Boleto)
            .where(Boleto.id_boleto == boleto.id_boleto,
                   db.or_(Boleto.status.is_(None), Boleto.status != "pago"))
            .values(status="pago", data_pagamento=data_pagamento)
            .execution_options(synchronize_session=False)
        ).rowcount
        if marcado != 1:
            db.session.rollback()
            raise ValueError("Este boleto já foi pago.")
        gasto = Gasto(id_usuario=boleto.id_usuario, id_categoria=boleto.id_categoria,
                      valor=valor, data=data_pagamento, descricao=boleto.descricao or "Boleto",
                      recorrente=bool(boleto.fixo),
                      tipo_pagamento="débito automático" if automatico else "boleto")
        db.session.add(gasto)
        db.session.flush()
        db.session.refresh(boleto)
        boleto.id_gasto = gasto.id_gasto
        proximo = None
        if boleto.fixo:
            vencimento = proximo_vencimento(boleto.vencimento, boleto.dia_vencimento)
            ja_existe = Boleto.query.filter_by(
                id_usuario=boleto.id_usuario, fixo=True, descricao=boleto.descricao,
                vencimento=vencimento).first()
            if ja_existe is None:
                proximo = Boleto(id_usuario=boleto.id_usuario, descricao=boleto.descricao,
                                 id_categoria=boleto.id_categoria, codigo_barras=None,
                                 valor=boleto.valor, vencimento=vencimento, status="pendente",
                                 fixo=True, debito_automatico=boleto.debito_automatico,
                                 dia_vencimento=boleto.dia_vencimento)
                db.session.add(proximo)
        db.session.commit()
        return gasto, proximo

    def pagar(self, id_boleto, dados, hoje=None):
        boleto = Boleto.buscar_por_id(id_boleto)
        if boleto is None:
            return None
        dados = dados if isinstance(dados, dict) else {}
        opcionais = validar_campos({"data_pagamento": data_iso,
                                    "valor": dinheiro(Decimal("0"), incluir_minimo=False)},
                                   dados, parcial=True)
        data_pagamento = opcionais.get("data_pagamento") or hoje or date.today()
        gasto, proximo = self._pagar(boleto, data_pagamento, opcionais.get("valor", boleto.valor))
        resposta = boleto.to_dict()
        resposta["gasto"] = gasto.to_dict()
        resposta["proximo"] = proximo.to_dict() if proximo else None
        return resposta

    def desfazer_pagamento(self, id_boleto):
        """Volta para pendente, apaga o gasto lançado e o próximo boleto fixo
        criado pelo pagamento (se ainda estiver pendente)."""
        boleto = Boleto.buscar_por_id(id_boleto)
        if boleto is None:
            return None
        if boleto.status != "pago":
            raise ValueError("Este boleto não está pago.")
        if boleto.id_gasto:
            gasto = db.session.get(Gasto, boleto.id_gasto)
            if gasto is not None and gasto.id_usuario == boleto.id_usuario:
                db.session.delete(gasto)
        if boleto.fixo:
            proximo = Boleto.query.filter_by(
                id_usuario=boleto.id_usuario, fixo=True, descricao=boleto.descricao, status="pendente",
                vencimento=proximo_vencimento(boleto.vencimento, boleto.dia_vencimento)).first()
            if proximo is not None:
                db.session.delete(proximo)
        boleto.status, boleto.data_pagamento, boleto.id_gasto = "pendente", None, None
        db.session.commit()
        return boleto.to_dict()

    # ---- rotina ao abrir as telas ---------------------------------------
    def processar(self, id_usuario, hoje=None):
        """Lança os débitos automáticos vencidos e cria avisos de vencimento.
        Retorna quantos pagamentos automáticos foram lançados."""
        hoje = hoje or date.today()
        pagos = 0
        for _ in range(MAX_MESES_ATRASADOS):
            vencidos = (Boleto.query
                        .filter(Boleto.id_usuario == id_usuario, Boleto.debito_automatico.is_(True),
                                db.or_(Boleto.status.is_(None), Boleto.status != "pago"),
                                Boleto.vencimento <= hoje)
                        .order_by(Boleto.vencimento).all())
            if not vencidos:
                break
            for boleto in vencidos:
                try:
                    self._pagar(boleto, boleto.vencimento, boleto.valor, automatico=True)
                    pagos += 1
                except ValueError:
                    db.session.rollback()   # outro processo pagou antes, ou sem categoria
        self._avisar_vencimentos(id_usuario, hoje)
        return {"pagos_automaticamente": pagos}

    def _avisar_vencimentos(self, id_usuario, hoje):
        pendentes = (Boleto.query
                     .filter(Boleto.id_usuario == id_usuario, Boleto.debito_automatico.is_(False),
                             db.or_(Boleto.status.is_(None), Boleto.status != "pago"))
                     .all())
        for boleto in pendentes:
            dias = (boleto.vencimento - hoje).days
            nome = boleto.descricao or "sem nome"
            if dias < 0:
                mensagem = (f'O boleto "{nome}" ({brl(boleto.valor)}) venceu em '
                            f"{boleto.vencimento:%d/%m/%Y} e ainda não foi pago.")
            elif dias <= DIAS_AVISO:
                quando = "hoje" if dias == 0 else ("amanhã" if dias == 1 else f"em {dias} dias")
                mensagem = (f'O boleto "{nome}" ({brl(boleto.valor)}) vence {quando}, '
                            f"{boleto.vencimento:%d/%m/%Y}.")
            else:
                continue
            # Um aviso de cada tipo por boleto: "vence em X" e depois "venceu".
            marca = f"{boleto.vencimento:%d/%m/%Y}"
            tipo_aviso = "venceu" if dias < 0 else "vence"
            existe = Alerta.query.filter(
                Alerta.id_usuario == id_usuario, Alerta.tipo == "boleto",
                Alerta.mensagem.like(f'O boleto "{nome}"%{tipo_aviso}%{marca}%')).first()
            if existe is None:
                db.session.add(Alerta(id_usuario=id_usuario, tipo="boleto", mensagem=mensagem,
                                      visualizado=False))
        db.session.commit()

    def proximos_vencimentos(self, id_usuario):
        return self.repository.proximos_vencimentos(id_usuario)
