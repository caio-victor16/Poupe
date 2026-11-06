"""Formato único para novas senhas; compatibilidade temporária com contas antigas."""
import hmac
from werkzeug.security import generate_password_hash, check_password_hash

METHOD = "scrypt:32768:8:1"


def validar_senha(senha):
    if not isinstance(senha, str) or not 1 <= len(senha) <= 1024:
        raise ValueError("A senha deve ser um texto de 1 a 1024 caracteres.")


def gerar_hash(senha):
    validar_senha(senha)
    return generate_password_hash(senha, method=METHOD)


def senha_tem_hash(valor):
    # Não reinterpretar um hash inválido como senha em texto puro.
    return valor.startswith(("scrypt:", "pbkdf2:"))


def conferir_senha(armazenada, informada):
    validar_senha(informada)
    if senha_tem_hash(armazenada):
        try:
            return check_password_hash(armazenada, informada)
        except (ValueError, TypeError):
            return False
    return hmac.compare_digest(armazenada.encode("utf-8"), informada.encode("utf-8"))
