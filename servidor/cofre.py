
import io
import secrets
import zipfile

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


FORMATO = b"USBLAB01"
TAMANHO_SALT = 16
TAMANHO_NONCE = 12


def derivar_chave(senha: str, salt: bytes) -> bytes:
    if not senha or len(senha) < 12:
        raise ValueError(
            "Use uma senha com pelo menos 12 caracteres."
        )

    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**15,
        r=8,
        p=1,
    )

    return kdf.derive(senha.encode("utf-8"))


def criptografar(dados: bytes, senha: str) -> bytes:
    salt = secrets.token_bytes(TAMANHO_SALT)
    nonce = secrets.token_bytes(TAMANHO_NONCE)
    chave = derivar_chave(senha, salt)

    cifrador = AESGCM(chave)
    conteudo_cifrado = cifrador.encrypt(
        nonce, dados, FORMATO
    )

    return FORMATO + salt + nonce + conteudo_cifrado


def descriptografar(cofre: bytes, senha: str) -> bytes:
    tamanho_cabecalho = (
        len(FORMATO) + TAMANHO_SALT + TAMANHO_NONCE
    )

    if (
        len(cofre) <= tamanho_cabecalho
        or not cofre.startswith(FORMATO)
    ):
        raise ValueError("Arquivo de cofre inválido.")

    inicio = len(FORMATO)
    salt = cofre[inicio:inicio + TAMANHO_SALT]

    inicio_nonce = inicio + TAMANHO_SALT
    nonce = cofre[
        inicio_nonce:inicio_nonce + TAMANHO_NONCE
    ]

    conteudo_cifrado = cofre[tamanho_cabecalho:]
    chave = derivar_chave(senha, salt)

    try:
        return AESGCM(chave).decrypt(
            nonce, conteudo_cifrado, FORMATO
        )
    except InvalidTag:
        raise ValueError(
            "Senha incorreta ou arquivo alterado."
        ) from None


def criar_arquivo_zip(arquivos) -> bytes:
    memoria = io.BytesIO()

    with zipfile.ZipFile(
        memoria, "w", zipfile.ZIP_DEFLATED
    ) as arquivo_zip:
        for arquivo in arquivos:
            nome = arquivo.filename

            if not nome or nome.endswith("/"):
                continue

            # Guarda apenas o nome, sem caminhos enviados pelo cliente.
            nome_seguro = nome.replace("\\", "/").split("/")[-1]

            if nome_seguro in ("", ".", ".."):
                continue

            conteudo = arquivo.read()
            arquivo_zip.writestr(nome_seguro, conteudo)

    return memoria.getvalue()
