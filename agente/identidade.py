
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey
)


# CAMINHOS DA IDENTIDADE
PASTA = Path.home() / ".usb_security_lab"

CHAVE_PRIVADA = PASTA / "identidade_privada.pem"
CHAVE_PUBLICA = PASTA / "identidade_publica.bin"


def preparar_identidade():
    """
    Cria ou carrega a identidade criptográfica
    deste computador.
    """

    PASTA.mkdir(parents=True, exist_ok=True)

    if CHAVE_PRIVADA.exists():

        chave = serialization.load_pem_private_key(
            CHAVE_PRIVADA.read_bytes(),
            password=None
        )

        if not isinstance(chave, Ed25519PrivateKey):
            raise ValueError(
                "A identidade armazenada não é Ed25519."
            )

    else:

        chave = Ed25519PrivateKey.generate()

        dados = chave.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        # Impede sobrescrever uma identidade existente.
        with CHAVE_PRIVADA.open("xb") as arquivo:
            arquivo.write(dados)

    chave_publica = chave.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )

    CHAVE_PUBLICA.write_bytes(chave_publica)

    return chave_publica.hex()


def assinar_desafio(desafio_hex):
    """
    Assina um desafio de 32 bytes usando
    a chave privada local.
    """

    if not isinstance(desafio_hex, str):
        raise ValueError("Desafio inválido.")

    try:
        desafio = bytes.fromhex(desafio_hex)
    except ValueError as erro:
        raise ValueError(
            "O desafio deve estar em hexadecimal."
        ) from erro

    if len(desafio) != 32:
        raise ValueError(
            "O desafio deve ter exatamente 32 bytes."
        )

    chave_privada = serialization.load_pem_private_key(
        CHAVE_PRIVADA.read_bytes(),
        password=None
    )

    if not isinstance(chave_privada, Ed25519PrivateKey):
        raise ValueError("Identidade privada inválida.")

    assinatura = chave_privada.sign(desafio)

    return assinatura.hex()


if __name__ == "__main__":
    preparar_identidade()
    print("Identidade do computador preparada com sucesso.")
