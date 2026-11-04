import sys
import requests
from pathlib import Path

sys.path.insert(0, str(Path("agente").resolve()))

from identidade import preparar_identidade, assinar_desafio

SERVIDOR = "http://127.0.0.1:5000"

# 1. Preparar identidade do computador
chave_publica = preparar_identidade()

# 2. Solicitar cadastro
resposta = requests.post(
    f"{SERVIDOR}/api/agente/cadastro",
    json={
        "nome": "Computador de Teste",
        "chave_publica": chave_publica
    },
    timeout=5
)
resposta.raise_for_status()

identificador = resposta.json()["identificador"]
print("1. Cadastro solicitado: True")

# 3. Solicitar desafio
resposta = requests.post(
    f"{SERVIDOR}/api/agente/cadastro/{identificador}/desafio",
    timeout=5
)
resposta.raise_for_status()

desafio = resposta.json()["desafio"]
print("2. Desafio recebido: True")

# 4. Assinar desafio
assinatura = assinar_desafio(desafio)
print("3. Desafio assinado:", len(bytes.fromhex(assinatura)) == 64)

# 5. Verificar identidade
resposta = requests.post(
    f"{SERVIDOR}/api/agente/cadastro/{identificador}/verificar",
    json={"assinatura": assinatura},
    timeout=5
)
resposta.raise_for_status()

print("4. Identidade verificada:", resposta.status_code == 200)

# 6. Testar proteção contra reutilização
resposta = requests.post(
    f"{SERVIDOR}/api/agente/cadastro/{identificador}/verificar",
    json={"assinatura": assinatura},
    timeout=5
)

print("5. Reutilização bloqueada:", resposta.status_code == 403)

print("\nTESTE FINALIZADO")
