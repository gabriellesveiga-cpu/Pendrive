
import os
import ctypes
import secrets
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

NOME_CHAVE_USB = "USB_SECURITY_LAB.key"

ARQUIVO_CHAVE_PUBLICA = (
    Path(__file__).resolve().parent / "chave_publica_usb.bin"
)


def encontrar_pendrives():
    if os.name != "nt":
        raise RuntimeError("Este agente foi preparado para Windows.")

    kernel32 = ctypes.windll.kernel32
    kernel32.GetLogicalDrives.restype = ctypes.c_uint32
    kernel32.GetDriveTypeW.argtypes = [ctypes.c_wchar_p]
    kernel32.GetDriveTypeW.restype = ctypes.c_uint

    unidades_ativas = kernel32.GetLogicalDrives()
    pendrives = []

    for indice in range(26):
        if not (unidades_ativas & (1 << indice)):
            continue

        letra = chr(ord("A") + indice)
        caminho = Path(f"{letra}:\\")

        if kernel32.GetDriveTypeW(str(caminho)) == 2:
            pendrives.append(caminho)

    return pendrives


def pendrive_autorizado():
    if not ARQUIVO_CHAVE_PUBLICA.exists():
        raise FileNotFoundError(
            "A chave pública não foi encontrada na pasta do agente."
        )

    chave_publica_bytes = ARQUIVO_CHAVE_PUBLICA.read_bytes()

    if len(chave_publica_bytes) != 32:
        raise ValueError("A chave pública está inválida.")

    chave_publica = Ed25519PublicKey.from_public_bytes(
        chave_publica_bytes
    )

    for unidade in encontrar_pendrives():
        arquivo_chave = unidade / NOME_CHAVE_USB

        try:
            chave_privada_bytes = arquivo_chave.read_bytes()

            if len(chave_privada_bytes) != 32:
                continue

            chave_privada = Ed25519PrivateKey.from_private_bytes(
                chave_privada_bytes
            )

            desafio = secrets.token_bytes(32)
            assinatura = chave_privada.sign(desafio)

            chave_publica.verify(assinatura, desafio)

            return True

        except (OSError, InvalidSignature, ValueError):
            continue

    return False


def consultar_autorizacao():
    """
    Consulta a autorização do pendrive sem expor
    informações sobre a chave privada.
    """
    try:
        autorizado = pendrive_autorizado()

        return {
            "autorizado": autorizado,
            "mensagem": (
                "Pendrive autorizado."
                if autorizado
                else "Pendrive não autorizado ou ausente."
            )
        }

    except (OSError, RuntimeError, ValueError) as erro:
        return {
            "autorizado": False,
            "mensagem": "Não foi possível verificar o pendrive.",
            "tipo_erro": type(erro).__name__
        }
