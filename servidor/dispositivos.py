
import json
import secrets
from pathlib import Path
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PublicKey
)
from cryptography.exceptions import InvalidSignature


ARQUIVO = Path(__file__).resolve().parent / "dispositivos.json"


class GerenciadorDispositivos:
    def __init__(self):
        self.dispositivos = self.carregar()

    def carregar(self):
        if not ARQUIVO.exists():
            return {}

        with open(ARQUIVO, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)

    def salvar(self):
        with open(ARQUIVO, "w", encoding="utf-8") as arquivo:
            json.dump(
                self.dispositivos,
                arquivo,
                indent=4,
                ensure_ascii=False
            )

   
    def cadastrar(self, nome, chave_publica_hex):
        """
        Registra um dispositivo inicialmente desativado.

        A ativação deverá ocorrer somente após
        verificação criptográfica e aprovação
        administrativa.
        """

        if not isinstance(nome, str) or not nome.strip():
            raise ValueError("Nome do computador inválido.")

        if not isinstance(chave_publica_hex, str):
            raise ValueError("Chave pública inválida.")

        try:
            chave_bytes = bytes.fromhex(chave_publica_hex)

            if len(chave_bytes) != 32:
                raise ValueError("Chave pública inválida.")

            Ed25519PublicKey.from_public_bytes(chave_bytes)

        except ValueError as erro:
            raise ValueError(
                "Formato da chave pública inválido."
            ) from erro

        # Impede cadastrar novamente a mesma chave.
        for identificador, dados in self.dispositivos.items():
            if dados["chave_publica"] == chave_publica_hex.lower():
                return identificador

        identificador = secrets.token_urlsafe(16)

        self.dispositivos[identificador] = {
            "nome": nome.strip()[:100],
            "chave_publica": chave_publica_hex.lower(),
            "cadastrado_em": datetime.now(
                timezone.utc
            ).isoformat(),
            "ativo": False
        }

        self.salvar()

        return identificador


    def verificar_assinatura(
        self,
        identificador,
        mensagem,
        assinatura_hex
    ):
        dispositivo = self.dispositivos.get(identificador)

        if not dispositivo or not dispositivo["ativo"]:
            return False

        try:
            chave = Ed25519PublicKey.from_public_bytes(
                bytes.fromhex(dispositivo["chave_publica"])
            )

            chave.verify(
                bytes.fromhex(assinatura_hex),
                mensagem.encode("utf-8")
            )

            return True

        except (ValueError, InvalidSignature):
            return False

    def desativar(self, identificador):
        if identificador not in self.dispositivos:
            return False

        self.dispositivos[identificador]["ativo"] = False
        self.salvar()

        return True
