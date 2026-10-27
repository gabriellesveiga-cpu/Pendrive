
from pathlib import Path
import platform
import socket

import psutil
from flask import Flask, jsonify, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
PAINEL_DIR = BASE_DIR.parent / "painel"

app = Flask(
    __name__,
    static_folder=str(PAINEL_DIR),
    static_url_path="/static"
)


@app.route("/")
def inicio():
    return send_from_directory(str(PAINEL_DIR), "index.html")


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


if __name__ == "__main__":
    print("USB Security Lab iniciado.")
    print("Abra http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
