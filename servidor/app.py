
from pathlib import Path
import ctypes
import hashlib
import io
import os
import platform
import socket

import psutil
from flask import (
    Flask,
    jsonify,
    request,
    send_file,
    send_from_directory,
)
from werkzeug.exceptions import RequestEntityTooLarge

from cofre import (
    criptografar,
    descriptografar,
    criar_arquivo_zip,
)

from historico import registrar_atividade, listar_atividades

BASE_DIR = Path(__file__).resolve().parent
PAINEL_DIR = BASE_DIR.parent / "painel"

app = Flask(__name__)

# Limite total de cada requisição enviada ao servidor.
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

# Limite individual para a análise inicial de arquivos.
MAX_ARQUIVO_ANALISE = 25 * 1024 * 1024


@app.errorhandler(RequestEntityTooLarge)
def arquivo_muito_grande(erro):
    return jsonify({
        "erro": "O envio ultrapassou o limite de 100 MB."
    }), 413


# --------------------------------------------------
# PAINEL
# --------------------------------------------------

@app.route("/")
def inicio():
    registrar_atividade(
        "sistema",
        "Painel do USB Security Lab acessado",
    )

    return send_from_directory(str(PAINEL_DIR), "index.html")


@app.route("/style.css")
def estilo():
    return send_from_directory(str(PAINEL_DIR), "style.css")


@app.route("/app.js")
def javascript():
    return send_from_directory(str(PAINEL_DIR), "app.js")


# --------------------------------------------------
# STATUS DO COMPUTADOR
# --------------------------------------------------

@app.route("/api/status")
def status():
    memoria = psutil.virtual_memory()

    try:
        disco = psutil.disk_usage("C:\\")
        disco_info = {
            "disco_percentual": disco.percent,
            "disco_livre_gb": round(
                disco.free / (1024 ** 3), 2
            ),
        }
    except OSError:
        disco_info = {
            "disco_percentual": None,
            "disco_livre_gb": None,
        }

    return jsonify({
        "computador": socket.gethostname(),
        "sistema": platform.system(),
        "versao": platform.release(),
        "memoria_percentual": memoria.percent,
        "memoria_total_gb": round(
            memoria.total / (1024 ** 3), 2
        ),
        **disco_info,
    })


# --------------------------------------------------
# DETECÇÃO DE UNIDADES REMOVÍVEIS NO WINDOWS
# --------------------------------------------------

@app.route("/api/usb")
def listar_usb():
    if os.name != "nt":
        return jsonify({
            "detectados": [],
            "aviso": (
                "Esta versão da detecção foi preparada "
                "para o Windows."
            ),
        })

    kernel32 = ctypes.windll.kernel32
    kernel32.GetLogicalDrives.restype = ctypes.c_uint32
    kernel32.GetDriveTypeW.argtypes = [ctypes.c_wchar_p]
    kernel32.GetDriveTypeW.restype = ctypes.c_uint

    unidades = []
    letras_ativas = kernel32.GetLogicalDrives()

    # DRIVE_REMOVABLE = 2
    for indice in range(26):
        if not (letras_ativas & (1 << indice)):
            continue

        letra = chr(ord("A") + indice)
        caminho = f"{letra}:\\"
        tipo = kernel32.GetDriveTypeW(caminho)

        if tipo == 2:
            try:
                disco = psutil.disk_usage(caminho)
                unidades.append({
                    "letra": caminho,
                    "total_gb": round(
                        disco.total / (1024 ** 3), 2
                    ),
                    "livre_gb": round(
                        disco.free / (1024 ** 3), 2
                    ),
                })
            except OSError:
                unidades.append({
                    "letra": caminho,
                    "total_gb": None,
                    "livre_gb": None,
                })

    return jsonify({
        "total": len(unidades),
        "detectados": unidades,
        "aviso": (
            "Alguns dispositivos USB podem ser classificados "
            "pelo Windows como discos fixos e não aparecer aqui."
        ),
    })


# --------------------------------------------------
# ANÁLISE INICIAL DE ARQUIVOS
# --------------------------------------------------

EXTENSOES_ATENCAO = {
    ".exe", ".bat", ".cmd", ".ps1", ".vbs",
    ".js", ".scr", ".msi", ".hta", ".dll",
}


@app.route("/api/analisar", methods=["POST"])
def analisar_arquivos():
    arquivos = request.files.getlist("arquivos")

    arquivos = [
        arquivo for arquivo in arquivos
        if arquivo.filename
    ]

    if not arquivos:
        return jsonify({
            "erro": "Selecione pelo menos um arquivo."
        }), 400

    resultados = []

    for arquivo in arquivos:
        nome_original = arquivo.filename or "arquivo_sem_nome"
        nome = nome_original.replace("\\", "/").split("/")[-1]

        conteudo = arquivo.stream.read(
            MAX_ARQUIVO_ANALISE + 1
        )

        if len(conteudo) > MAX_ARQUIVO_ANALISE:
            resultados.append({
                "nome": nome,
                "situacao": "Não analisado",
                "detalhe": (
                    "O arquivo ultrapassa o limite de "
                    "25 MB para esta análise."
                ),
            })
            continue

        if not conteudo:
            resultados.append({
                "nome": nome,
                "tamanho_bytes": 0,
                "situacao": "Vazio",
                "detalhe": "O arquivo está vazio.",
            })
            continue

        extensao = Path(nome).suffix.lower()
        sha256 = hashlib.sha256(conteudo).hexdigest()

        if extensao in EXTENSOES_ATENCAO:
            situacao = "Atenção"
            detalhe = (
                "Este tipo de arquivo pode executar código. "
                "A extensão, sozinha, não comprova que "
                "seja malicioso."
            )
        else:
            situacao = "Análise inicial"
            detalhe = (
                "Nenhuma regra básica foi acionada. "
                "Isso não garante que o arquivo seja seguro."
            )

        resultados.append({
            "nome": nome,
            "tamanho_bytes": len(conteudo),
            "sha256": sha256,
            "situacao": situacao,
            "detalhe": detalhe,
        })

registrar_atividade(
    "analise",
    "Análise inicial de arquivos concluída",
    {
        "total": len(resultados),
        "atencao": sum(
            1 for item in resultados
            if item["situacao"] == "Atenção"
        ),
        "nao_analisados": sum(
            1 for item in resultados
            if item["situacao"] == "Não analisado"
        ),
    },
)

return jsonify({
    "total": len(resultados),
    "resultados": resultados,
})


# --------------------------------------------------
# CRIAR COFRE CRIPTOGRAFADO
# --------------------------------------------------

@app.route("/api/cofre/criar", methods=["POST"])
def criar_cofre():
    arquivos = request.files.getlist("arquivos")
    senha = request.form.get("senha", "")

    if not arquivos or not any(a.filename for a in arquivos):
        return jsonify({
            "erro": "Selecione pelo menos um arquivo."
        }), 400

    if len(senha) < 12:
        return jsonify({
            "erro": "A senha deve ter pelo menos 12 caracteres."
        }), 400

    try:
        pacote_zip = criar_arquivo_zip(arquivos)
        conteudo_cifrado = criptografar(pacote_zip, senha)

        return send_file(
            io.BytesIO(conteudo_cifrado),
            mimetype="application/octet-stream",
            as_attachment=True,
            download_name="meu_cofre.usblab",
        )

    except (ValueError, OSError) as erro:
        return jsonify({"erro": str(erro)}), 400


# --------------------------------------------------
# ABRIR COFRE CRIPTOGRAFADO
# --------------------------------------------------

@app.route("/api/cofre/abrir", methods=["POST"])
def abrir_cofre():
    arquivo = request.files.get("cofre")
    senha = request.form.get("senha", "")

    if not arquivo or not arquivo.filename:
        return jsonify({
            "erro": "Selecione um arquivo de cofre."
        }), 400

    if not senha:
        return jsonify({
            "erro": "Informe a senha do cofre."
        }), 400

    try:
        conteudo_cifrado = arquivo.read()
        pacote_zip = descriptografar(
            conteudo_cifrado, senha
        )

        return send_file(
            io.BytesIO(pacote_zip),
            mimetype="application/zip",
            as_attachment=True,
            download_name="projetos_recuperados.zip",
        )

    except ValueError as erro:
        return jsonify({"erro": str(erro)}), 400



# --------------------------------------------------
# HISTÓRICO DE ATIVIDADES
# --------------------------------------------------

@app.route("/api/historico")
def consultar_historico():
    return jsonify({
        "total": len(listar_atividades()),
        "atividades": listar_atividades(),
    })


# --------------------------------------------------
# INICIAR SOMENTE NO COMPUTADOR LOCAL
# --------------------------------------------------

if __name__ == "__main__":
    print("USB Security Lab iniciado.")
    print("Abra http://127.0.0.1:5000")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
    )
