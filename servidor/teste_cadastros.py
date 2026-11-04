from cadastros import GerenciadorCadastros
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

def testar():
    gerenciador = GerenciadorCadastros()

    privada = Ed25519PrivateKey.generate()
    publica = privada.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    ).hex()

    identificador = gerenciador.solicitar("Computador Teste", publica)

    print("1. Cadastro criado:", bool(identificador))
    print("2. Cadastro pendente:", len(gerenciador.listar_pendentes()) == 1)
    print("3. Aprovação sem verificação bloqueada:", gerenciador.aprovar(identificador) is None)

    gerenciador.confirmar_identidade(identificador)
    aprovado = gerenciador.aprovar(identificador)

    print("4. Cadastro aprovado:", aprovado is not None)
    print("5. Aprovação duplicada bloqueada:", gerenciador.aprovar(identificador) is None)

if __name__ == "__main__":
    testar()
