
from pathlib import Path
import ctypes
import os
import sys

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)
from cryptography.hazmat.primitives import serialization


BASE_DIR = Path(__file__).resolve().parent

NOME_CHAVE_USB = "USB_SECURITY_LAB.key"
ARQUIVO_CHAVE_PUBLICA = BASE_DIR / "chave_publica_usb.bin"


def encontrar_pendrives():
    if os.name != "nt":
        raise RuntimeError("Esta versão foi preparada para Windows.")

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
        caminho = f"{letra}:\\"

        # 2 = DRIVE_REMOVABLE
        if kernel32.GetDriveTypeW(caminho) == 2:
            pendrives.append(Path(caminho))

    return pendrives


def configurar():
    if ARQUIVO_CHAVE_PUBLICA.exists():
        print("Já existe uma chave pública configurada.")
        print("Não vou substituir a chave existente.")
        return

    pendrives = encontrar_pendrives()

    if not pendrives:
        print("Nenhum pendrive removível foi encontrado.")
        print("Conecte o pendrive e tente novamente.")
        return

    print("\nPendrives encontrados:\n")

    for indice, unidade in enumerate(pendrives, start=1):
        print(f"{indice} - {unidade}")

    escolha = input("\nEscolha o número do pendrive: ").strip()

    if not escolha.isdigit():
        print("Escolha inválida.")
        return

    indice = int(escolha) - 1

    if indice < 0 or indice >= len(pendrives):
        print("Número fora da lista.")
        return

    pendrive = pendrives[indice]
    arquivo_privado = pendrive / NOME_CHAVE_USB

    if arquivo_privado.exists():
        print("Este pendrive já possui um arquivo de chave.")
        print("Não vou sobrescrever o arquivo.")
        return

    try:
        chave_privada = Ed25519PrivateKey.generate()

        chave_privada_bytes = chave_privada.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )

        chave_publica_bytes = chave_privada.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

        # Cria o arquivo no pendrive sem sobrescrever outro.
        with arquivo_privado.open("xb") as arquivo:
            arquivo.write(chave_privada_bytes)

        # Guarda a chave pública no projeto.
        with ARQUIVO_CHAVE_PUBLICA.open("xb") as arquivo:
            arquivo.write(chave_publica_bytes)

        print("\nChave criada com sucesso!")
        print(f"Pendrive autorizado: {pendrive}")
        print(f"Chave privada: {arquivo_privado}")
        print(f"Chave pública: {ARQUIVO_CHAVE_PUBLICA}")

        print("\nIMPORTANTE:")
        print("Não apague nem compartilhe a chave privada.")
        print("Não formate o pendrive sem fazer uma cópia segura.")
        print("A chave pública será instalada no computador controlado.")

    except OSError as erro:
        print(f"Erro ao gravar as chaves: {erro}")

        if arquivo_privado.exists():
            print(
                "Atenção: o arquivo privado pode ter sido criado. "
                "Não tente gerar outra chave sem verificar os arquivos."
            )


if __name__ == "__main__":
    configurar()
