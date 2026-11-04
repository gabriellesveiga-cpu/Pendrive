
import os
import requests
from urllib.parse import urlparse


class ComunicacaoServidor:
    def __init__(self, endereco_servidor=None):
        endereco = endereco_servidor or os.getenv(
            "USB_LAB_SERVIDOR",
            "http://127.0.0.1:5000"
        )

        self.servidor = endereco.rstrip("/")

        url = urlparse(self.servidor)

        if url.scheme not in ("http", "https"):
            raise ValueError("Endereço do servidor inválido.")

        if not url.hostname:
            raise ValueError("Servidor não informado.")

        if url.scheme == "http" and url.hostname not in (
            "127.0.0.1",
            "localhost"
        ):
            raise ValueError(
                "Conexões fora do computador exigem HTTPS."
            )

    def verificar_conexao(self):
        try:
            resposta = requests.get(
                f"{self.servidor}/status",
                timeout=5
            )

            resposta.raise_for_status()

            return {
                "conectado": True,
                "dados": resposta.json()
            }

        except (requests.RequestException, ValueError) as erro:
            return {
                "conectado": False,
                "erro": str(erro)
            }


if __name__ == "__main__":
    comunicacao = ComunicacaoServidor()

    resultado = comunicacao.verificar_conexao()

    if resultado["conectado"]:
        print("Conexão com o servidor estabelecida!")
        print(resultado["dados"])
    else:
        print("Não foi possível conectar ao servidor.")
        print(resultado["erro"])
