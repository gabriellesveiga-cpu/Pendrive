
from pathlib import Path
import platform
import socket

import psutil
import hashlib
from flask import Flask, jsonify, send_from_directory, request

BASE_DIR = Path(__file__).resolve().parent
PAINEL_DIR = BASE_DIR.parent / "painel"

app = Flask(__name__)


@app.route("/")
def inicio():
    return send_from_directory(str(PAINEL_DIR), "index.html")


@app.route("/style.css")
def estilo():
    return send_from_directory(str(PAINEL_DIR), "style.css")


@app.route("/app.js")
def javascript():
    return send_from_directory(str(PAINEL_DIR), "app.js")


@app.route("/api/status")
def status():
    memoria = psutil.virtual_memory()
    disco = psutil.disk_usage("C:\\")

    return jsonify({
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
    })


EXTENSOES_ATENCAO = {
    ".exe", ".bat", ".cmd", ".ps1", ".vbs",
    ".js", ".scr", ".msi", ".hta", ".dll"
}


@app.route("/api/analisar", methods=["POST"])
def analisar_arquivos():
    arquivos = request.files.getlist("arquivos")

    if not arquivos or all(not arquivo.filename for arquivo in arquivos):
        return jsonify({
            "erro": "Selecione pelo menos um arquivo."
        }), 400

    resultados = []

    for arquivo in arquivos:
        nome = arquivo.filename or "arquivo_sem_nome"
        conteudo = arquivo.read()

        if not conteudo:
            resultados.append({
                "nome": nome,
                "situacao": "Vazio",
                "detalhe": "O arquivo está vazio."
            })
            continue

        extensao = "." + nome.rsplit(".", 1)[-1].lower() if "." in nome else ""

        sha256 = hashlib.sha256(conteudo).hexdigest()

        if extensao in EXTENSOES_ATENCAO:
            situacao = "Atenção"
            detalhe = (
                "Este tipo de arquivo pode executar código. "
                "A extensão, sozinha, não comprova que seja malicioso."
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
            "detalhe": detalhe
        })

    return jsonify({
        "total": len(resultados),
        "resultados": resultados
    })
    
if __name__ == "__main__":
    print("USB Security Lab iniciado.")
    print("Abra http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
