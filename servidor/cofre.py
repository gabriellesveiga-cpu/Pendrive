
import io
import secrets
import zipfile
from collections import Counter

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


FORMATO = b"USBLAB01"
TAMANHO_SALT = 16
TAMANHO_NONCE = 12

# Limites para reduzir o risco de consumo excessivo de memória.
MAX_ARQUIVOS = 200
MAX_ARQUIVO_BYTES = 25 * 1024 * 1024
MAX_TOTAL_BYTES = 90 * 1024 * 1024


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
    arquivos_validos = [
        arquivo
        for arquivo in arquivos
        if arquivo.filename and not arquivo.filename.endswith("/")
    ]

    if not arquivos_validos:
        raise ValueError("Selecione pelo menos um arquivo.")

    if len(arquivos_validos) > MAX_ARQUIVOS:
        raise ValueError(
            f"O limite é de {MAX_ARQUIVOS} arquivos por cofre."
        )

    memoria = io.BytesIO()
    nomes_usados = set()
    total_bytes = 0

    with zipfile.ZipFile(
        memoria, "w", zipfile.ZIP_DEFLATED
    ) as arquivo_zip:

        for arquivo in arquivos_validos:
            # Remove caminhos enviados pelo navegador.
            nome = arquivo.filename.replace("\\", "/").split("/")[-1]
            nome = nome.strip()

            if nome in ("", ".", ".."):
                raise ValueError("Um dos arquivos tem nome inválido.")

            conteudo = arquivo.stream.read(MAX_ARQUIVO_BYTES + 1)

            if len(conteudo) > MAX_ARQUIVO_BYTES:
                raise ValueError(
                    f"O arquivo '{nome}' ultrapassa o limite de 25 MB."
                )

            total_bytes += len(conteudo)

            if total_bytes > MAX_TOTAL_BYTES:
                raise ValueError(
                    "O total dos arquivos ultrapassa o limite de 90 MB."
                )

            # Evita nomes repetidos dentro do ZIP.
            nome_base = nome
            contador = 2

            while nome.casefold() in nomes_usados:
                partes = nome_base.rsplit(".", 1)

                if len(partes) == 2 and partes[0]:
                    nome = f"{partes[0]} ({contador}).{partes[1]}"
                else:
                    nome = f"{nome_base} ({contador})"

                contador += 1

            nomes_usados.add(nome.casefold())
            arquivo_zip.writestr(nome, conteudo)

    return memoria.getvalue()
