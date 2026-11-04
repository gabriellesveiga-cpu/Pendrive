
from cadastros import GerenciadorCadastros

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey
)

from cryptography.hazmat.primitives import serialization


def testar_cadastros():
    print("\n===== USB SECURITY LAB =====")
    print("TESTE DE CADASTRO DE DISPOSITIVOS\n")

    gerenciador = GerenciadorCadastros()

    # Criar identidade temporária de teste
    chave_privada = Ed25519PrivateKey.generate()

    chave_publica = chave_privada.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    ).hex()

    # TESTE 1 - Solicitar cadastro
    identificador = gerenciador.solicitar(
        "Computador de Teste",
        chave_publica
    )

    print(
        "1. Cadastro criado:",
        bool(identificador)
    )

    # TESTE 2 - Verificar cadastro pendente
    pendentes = gerenciador.listar_pendentes()

    print(
        "2. Cadastro pendente:",
        len(pendentes) == 1
    )

    # TESTE 3 - Identidade começa não verificada
    print(
        "3. Identidade não verificada:",
        pendentes[0]["identidade_verificada"] is False
    )

    # TESTE 4 - Bloquear aprovação sem verificação
    resultado = gerenciador.aprovar(identificador)

    print(
        "4. Aprovação sem verificação bloqueada:",
        resultado is None
    )

    # TESTE 5 - Confirmar identidade
    confirmado = gerenciador.confirmar_identidade(
        identificador
    )

    print(
        "5. Confirmação de identidade:",
        confirmado is True
    )

    # TESTE 6 - Aprovar após confirmação
    aprovado = gerenciador.aprovar(identificador)

    print(
        "6. Cadastro aprovado:",
        aprovado is not None
        and aprovado["status"] == "aprovado"
    )

    # TESTE 7 - Impedir aprovação duplicada
    segunda_aprovacao = gerenciador.aprovar(
        identificador
    )

    print(
        "7. Aprovação duplicada bloqueada:",
        segunda_aprovacao is None
    )

    print("\n===== TESTES FINALIZADOS =====")


if __name__ == "__main__":
    testar_cadastros()

