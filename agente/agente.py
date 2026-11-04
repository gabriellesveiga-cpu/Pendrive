
import platform
import socket

import psutil


def obter_informacoes_computador():
    """
    Obtém informações básicas do computador local.
    Não inicia servidor e não permite acesso remoto.
    """

    memoria = psutil.virtual_memory()
    disco = psutil.disk_usage("C:\\")

    return {
        "computador": socket.gethostname(),
        "sistema": platform.system(),
        "versao": platform.release(),
        "memoria_percentual": memoria.percent,
        "memoria_total_gb": round(
            memoria.total / (1024 ** 3), 2
        ),
        "disco_percentual": disco.percent,
        "disco_livre_gb": round(
            disco.free / (1024 ** 3), 2
        )
    }


if __name__ == "__main__":
    print("USB SECURITY LAB - INFORMAÇÕES DO COMPUTADOR")

    informacoes = obter_informacoes_computador()

    for chave, valor in informacoes.items():
        print(f"{chave}: {valor}")
