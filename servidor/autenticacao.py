
import secrets
import hmac
from datetime import datetime, timedelta, timezone


class GerenciadorAutenticacao:
    def __init__(self):
        self.tokens = {}

    def gerar_token(self, identificador, validade_minutos=10):
        token = secrets.token_urlsafe(32)

        expiracao = (
            datetime.now(timezone.utc)
            + timedelta(minutes=validade_minutos)
        )

        self.tokens[token] = {
            "identificador": identificador,
            "expiracao": expiracao
        }

        return token

    def verificar_token(self, token, identificador):
        if not isinstance(token, str):
            return False

        for token_salvo, dados in list(self.tokens.items()):
            if datetime.now(timezone.utc) >= dados["expiracao"]:
                del self.tokens[token_salvo]
                continue

            if (
                hmac.compare_digest(token, token_salvo)
                and dados["identificador"] == identificador
            ):
                return True

        return False

    def revogar_token(self, token):
        self.tokens.pop(token, None)
