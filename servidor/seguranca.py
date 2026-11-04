
import hmac
from functools import wraps
from pathlib import Path

from flask import request, jsonify, session

ARQUIVO_CHAVE = Path.home() / ".usb_security_lab_admin"

METODOS_ALTERACAO = {"POST", "PUT", "PATCH", "DELETE"}


def verificar_chave_admin():
    if not ARQUIVO_CHAVE.is_file():
        return False

    chave_correta = ARQUIVO_CHAVE.read_text(
        encoding="utf-8"
    ).strip()

    chave_recebida = request.headers.get("X-Admin-Key", "")

    if not chave_correta or not chave_recebida:
        return False

    return hmac.compare_digest(chave_recebida, chave_correta)


def verificar_sessao_admin():
    return session.get("admin") is True


def exigir_admin(funcao):
    @wraps(funcao)
    def protegida(*args, **kwargs):
        # Autenticação pela sessão do painel
        if verificar_sessao_admin():
            if request.method in METODOS_ALTERACAO:
                token_correto = session.get("csrf", "")
                token_recebido = request.headers.get("X-CSRF-Token", "")

                if (
                    not token_correto
                    or not token_recebido
                    or not hmac.compare_digest(
                        token_recebido, token_correto
                    )
                ):
                    return jsonify({
                        "erro": "Token CSRF inválido."
                    }), 403

            return funcao(*args, **kwargs)

        # Compatibilidade temporária com testes locais
        if (
            request.remote_addr in ("127.0.0.1", "::1")
            and verificar_chave_admin()
        ):
            return funcao(*args, **kwargs)

        return jsonify({
            "erro": "Acesso administrativo não autorizado."
        }), 401

    return protegida
