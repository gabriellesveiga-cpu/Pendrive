
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path("agente").resolve()))

from identidade import preparar_identidade, assinar_desafio


SERVIDOR = "http://127.0.0.1:5000"


def testar_autenticacao():
    print("\n===== USB SECURITY LAB =====")
    print("TESTE DE AUTENTICAÇÃO DO AGENTE\n")

    # Preparar identidade local
    chave_publica = preparar_identidade()

    # Carregar dispositivos cadastrados
    arquivo = Path("servidor/dispositivos.json")

    if not arquivo.exists():
        print("ERRO: Nenhum cadastro encontrado.")
        return

    dispositivos = json.loads(
        arquivo.read_text(encoding="utf-8")
    )

    # Encontrar dispositivo correspondente
    dispositivo_id = None

    for identificador, dados in dispositivos.items():
        if (
            dados.get("ativo") is True
            and dados.get("chave_publica") == chave_publica
        ):
            dispositivo_id = identificador
            break

    if not dispositivo_id:
        print("ERRO: Identidade não cadastrada ou inativa.")
        return

    print("1. Dispositivo cadastrado: True")

    # Solicitar desafio ao servidor
    resposta = requests.post(
        f"{SERVIDOR}/api/agente/autenticacao/desafio",
        json={"dispositivo_id": dispositivo_id},
        timeout=5
    )

    resposta.raise_for_status()

    desafio = resposta.json()["desafio"]

    print("2. Desafio recebido: True")

    # Assinar desafio
    assinatura = assinar_desafio(desafio)

    print(
        "3. Desafio assinado:",
        len(bytes.fromhex(assinatura)) == 64
    )

    # Enviar assinatura
    resposta = requests.post(
        f"{SERVIDOR}/api/agente/autenticacao/verificar",
        json={
            "dispositivo_id": dispositivo_id,
            "assinatura": assinatura
        },
        timeout=5
    )

    resposta.raise_for_status()

    dados = resposta.json()

    print(
        "4. Identidade autenticada:",
        dados.get("autenticado") is True
    )

    # Testar bloqueio de reutilização
    resposta = requests.post(
        f"{SERVIDOR}/api/agente/autenticacao/verificar",
        json={
            "dispositivo_id": dispositivo_id,
            "assinatura": assinatura
        },
        timeout=5
    )

    print(
        "5. Reutilização bloqueada:",
        resposta.status_code == 403
    )

    print("\n===== TESTE FINALIZADO =====")


if __name__ == "__main__":
    try:
        testar_autenticacao()
    except requests.RequestException as erro:
        print("Erro de comunicação:", erro)
    except (OSError, ValueError, KeyError) as erro:
        print("Erro no teste:", erro)

