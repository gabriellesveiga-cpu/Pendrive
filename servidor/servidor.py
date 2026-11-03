
import secrets
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO


# CONFIGURAÇÃO
app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(32)

socketio = SocketIO(
    app,
    cors_allowed_origins=[],
    async_mode="threading"
)

# Armazenamento das sessões durante a execução do servidor
sessoes = {}

# Caminho da pasta do painel
PAINEL_DIR = Path(__file__).resolve().parent.parent / "painel"


# ROTA INICIAL
@app.route("/")
def inicio():
    return jsonify({
        "mensagem": "USB Security Lab - Servidor online"
    })


# STATUS DO SERVIDOR
@app.route("/status")
def status():
    return jsonify({
        "servidor": "online"
    })


# CRIAR SOLICITAÇÃO DE SESSÃO
@app.route("/sessao", methods=["POST"])
def criar_sessao():
    dados = request.get_json(silent=True) or {}

    nome = dados.get("nome", "Computador desconhecido")

    identificador = secrets.token_urlsafe(16)

    sessoes[identificador] = {
        "identificador": identificador,
        "nome": nome,
        "criada_em": datetime.now(timezone.utc).isoformat(),
        "status": "aguardando_aprovacao"
    }

    return jsonify({
        "mensagem": "Solicitação criada.",
        "identificador": identificador
    }), 201


# LISTAR SOLICITAÇÕES PENDENTES
@app.route("/solicitacoes/pendentes")
def solicitacoes_pendentes():
    pendentes = [
        sessao
        for sessao in sessoes.values()
        if sessao["status"] == "aguardando_aprovacao"
    ]

    return jsonify({
        "solicitacoes": pendentes
    })


# LISTAR TODAS AS SESSÕES
@app.route("/sessoes")
def listar_sessoes():
    return jsonify({
        "sessoes": list(sessoes.values())
    })


# APROVAR SOLICITAÇÃO
@app.route("/sessao/<identificador>/aprovar", methods=["POST"])
def aprovar_sessao(identificador):
    sessao = sessoes.get(identificador)

    if not sessao:
        return jsonify({
            "erro": "Sessão não encontrada."
        }), 404

    if sessao["status"] != "aguardando_aprovacao":
        return jsonify({
            "erro": "Esta solicitação não está aguardando aprovação."
        }), 409

    sessao["status"] = "aprovada"

    return jsonify({
        "mensagem": "Sessão aprovada.",
        "identificador": identificador
    })


# RECUSAR SOLICITAÇÃO
@app.route("/sessao/<identificador>/recusar", methods=["POST"])
def recusar_sessao(identificador):
    sessao = sessoes.get(identificador)

    if not sessao:
        return jsonify({
            "erro": "Sessão não encontrada."
        }), 404

    if sessao["status"] != "aguardando_aprovacao":
        return jsonify({
            "erro": "Esta solicitação não está aguardando aprovação."
        }), 409

    sessao["status"] = "recusada"

    return jsonify({
        "mensagem": "Solicitação recusada.",
        "identificador": identificador
    })


# ENCERRAR SESSÃO
@app.route("/sessao/<identificador>/encerrar", methods=["POST"])
def encerrar_sessao(identificador):
    sessao = sessoes.get(identificador)

    if not sessao:
        return jsonify({
            "erro": "Sessão não encontrada."
        }), 404

    if sessao["status"] not in ("aprovada", "ativa"):
        return jsonify({
            "erro": "Esta sessão não está ativa."
        }), 409

    sessao["status"] = "encerrada"

    return jsonify({
        "mensagem": "Sessão encerrada.",
        "identificador": identificador
    })


# ABRIR PAINEL
@app.route("/painel")
def abrir_painel():
    return send_from_directory(
        PAINEL_DIR,
        "index.html"
    )


# CARREGAR CSS, JAVASCRIPT E OUTROS ARQUIVOS DO PAINEL
@app.route("/painel/<path:arquivo>")
def arquivos_painel(arquivo):
    return send_from_directory(
        PAINEL_DIR,
        arquivo
    )


# INICIAR SERVIDOR
if __name__ == "__main__":
    print("USB SECURITY LAB - SERVIDOR INICIADO")
    print(app.url_map)

    socketio.run(
        app,
        host="127.0.0.1",
        port=5000,
        debug=False
    )
