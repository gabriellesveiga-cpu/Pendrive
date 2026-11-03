
import time
from datetime import datetime

from .autorizacao import pendrive_autorizado

INTERVALO_VERIFICACAO = 1


def registrar(mensagem):
    horario = datetime.now().strftime("%H:%M:%S")
    print(f"[{horario}] {mensagem}", flush=True)


def iniciar_monitoramento():
    registrar("USB SECURITY LAB - MONITORAMENTO INICIADO")

    autorizado_anteriormente = False

    try:
        while True:
            try:
                autorizado = pendrive_autorizado()

            except Exception as erro:
                autorizado = False
                registrar(f"Erro na verificacao: {erro}")

            if autorizado and not autorizado_anteriormente:
                registrar("PENDRIVE AUTORIZADO!")
                registrar("Estado: ACESSO LIBERADO")

            elif not autorizado and autorizado_anteriormente:
                registrar("PENDRIVE REMOVIDO!")
                registrar("Estado: ACESSO BLOQUEADO")

            elif not autorizado and not autorizado_anteriormente:
                registrar("Aguardando pendrive autorizado...")

            autorizado_anteriormente = autorizado

            time.sleep(INTERVALO_VERIFICACAO)

    except KeyboardInterrupt:
        registrar("Monitoramento encerrado pelo usuario.")


if __name__ == "__main__":
    iniciar_monitoramento()
