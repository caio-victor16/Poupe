from decimal import Decimal

from backend.crud import dinheiro, email, telefone, texto, validar_campos
from backend.extensions import db
from backend.models.usuario import Usuario
from backend.passwords import gerar_hash, conferir_senha, senha_tem_hash
from backend import seguranca


class SenhaAtualIncorreta(ValueError):
    pass


# REV-004: com e-mail inexistente, confere a senha contra este hash para o
# login levar o mesmo tempo (senão o tempo revela quais e-mails existem).
HASH_FALSO = gerar_hash("poupe-usuario-inexistente")

# Item 12: renda pode ser zero (antes "0" era tratado como campo ausente);
# limite precisa ser maior que zero (com limite 0 todo gasto estoura o limite).
CAMPOS_USUARIO = {
    "nome": texto(100),
    "email": email,
    "renda_mensal": dinheiro(Decimal("0")),
    "limite_gastos": dinheiro(Decimal("0"), incluir_minimo=False),
}


class UsuarioService:
    def listar(self):
        return [u.to_dict() for u in Usuario.listar_todos()]

    def buscar_por_id(self, id_usuario):
        usuario = Usuario.buscar_por_id(id_usuario)
        return usuario.to_dict() if usuario else None

    def criar(self, dados):
        if not isinstance(dados, dict):
            raise ValueError("Informe um objeto JSON.")
        limpos = validar_campos(CAMPOS_USUARIO, dados)
        limpos.update(validar_campos({"telefone": telefone}, dados, parcial=True))
        if "senha" not in dados:
            raise ValueError("O campo 'senha' é obrigatório.")
        if Usuario.buscar_por_email(limpos["email"]):
            raise ValueError("Já existe um usuário cadastrado com este e-mail.")
        senha_hash = gerar_hash(dados["senha"])

        usuario = Usuario(senha=senha_hash, **limpos)
        usuario.salvar()
        return usuario.to_dict()

    def atualizar(self, id_usuario, dados):
        if not isinstance(dados, dict):
            raise ValueError("Informe um objeto JSON.")
        # Validar tudo antes de modificar qualquer atributo do usuário.
        limpos = validar_campos({**CAMPOS_USUARIO, "telefone": telefone}, dados, parcial=True)
        if "senha" in dados:
            limpos["senha"] = gerar_hash(dados["senha"])
        usuario = Usuario.buscar_por_id(id_usuario)
        if usuario is None:
            return None

        troca_email = "email" in limpos and limpos["email"] != usuario.email
        if troca_email:
            existente = Usuario.buscar_por_email(limpos["email"])
            if existente and existente.id_usuario != usuario.id_usuario:
                raise ValueError("Já existe outro usuário com este e-mail.")

        # REV-002: quem só tem o cookie (sem a senha) não pode tomar a conta.
        credenciais = "senha" in limpos or troca_email
        if credenciais:
            self._conferir_senha_atual(usuario, dados.get("senha_atual"))

        for campo, valor in limpos.items():
            setattr(usuario, campo, valor)
        if credenciais:
            seguranca.encerrar_outras_sessoes(usuario.id_usuario)
        db.session.commit()
        return usuario.to_dict()

    def _conferir_senha_atual(self, usuario, senha_atual):
        if not isinstance(senha_atual, str) or not senha_atual:
            raise ValueError("Informe a senha atual para trocar a senha ou o e-mail.")
        # Mesmo contador do login: impede adivinhar a senha por esta rota.
        regras = seguranca.regras_login(usuario.email)
        seguranca.exigir_liberado(regras)
        if not conferir_senha(usuario.senha, senha_atual):
            seguranca.registrar(*(chave for chave, _, _ in regras))
            raise SenhaAtualIncorreta("Senha atual incorreta.")

    def excluir(self, id_usuario):
        usuario = Usuario.buscar_por_id(id_usuario)
        if usuario is None:
            return False
        usuario.deletar()
        return True

    def autenticar(self, email, senha):
        usuario = Usuario.buscar_por_email(email)
        if usuario is None:
            conferir_senha(HASH_FALSO, senha)
            return None
        if not conferir_senha(usuario.senha, senha):
            return None
        if not senha_tem_hash(usuario.senha):
            usuario.senha = gerar_hash(senha)
            usuario.salvar()
        return usuario.to_dict()
