
import secrets
from datetime import datetime, timedelta, timezone

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


class GerenciadorDesafios:
    def __init__(self):
        self.desafios = {}

    def gerar(self, identificador):
        if not identificador:
            raise ValueError("Identificador obrigatório.")

        desafio = secrets.token_bytes(32)
        desafio_hex = desafio.hex()

        self.desafios[identificador] = {
            "desafio": desafio,
            "expiracao": datetime.now(timezone.utc) + timedelta(minutes=2)
        }

        return desafio_hex

    def verificar(self, identificador, chave_publica_hex, assinatura_hex):
        # O desafio é removido antes da verificação,
        # impedindo que seja reutilizado.
        dados = self.desafios.pop(identificador, None)

        if dados is None:
            return False

        if datetime.now(timezone.utc) >= dados["expiracao"]:
            return False

        try:
            chave_publica = Ed25519PublicKey.from_public_bytes(
                bytes.fromhex(chave_publica_hex)
            )

            assinatura = bytes.fromhex(assinatura_hex)

            chave_publica.verify(
                assinatura,
                dados["desafio"]
            )

            return True

        except (ValueError, InvalidSignature):
            return False

