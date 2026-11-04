
import secrets
from datetime import datetime, timezone
from pathlib import Path

from autenticacao import GerenciadorAutenticacao
from dispositivos import GerenciadorDispositivos
from cadastros import GerenciadorCadastros
from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO
from seguranca import exigir_admin
from login_painel import login_painel
from flask import session, redirect, url_for
from desafios import GerenciadorDesafios

# CONFIGURAÇÃO
app = Flask(__name__)
app.config["SECRET_KEY"] = secrets.token_hex(32)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
app.config["PERMANENT_SESSION_LIFETIME"] = 1800

app.register_blueprint(login_painel)

socketio = SocketIO(
    app,
    cors_allowed_origins=[],
    async_mode="threading"
)

# Armazenamento das sessões durante a execução do servidor
sessoes = {}
autenticacao = GerenciadorAutenticacao()
dispositivos = GerenciadorDispositivos()
cadastros = GerenciadorCadastros()
desafios = GerenciadorDesafios()

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
@exigir_admin
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
@exigir_admin
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
@exigir_admin
def listar_sessoes():
    return jsonify({
        "sessoes": list(sessoes.values())
    })


# APROVAR SOLICITAÇÃO
@app.route("/sessao/<identificador>/aprovar", methods=["POST"])
@exigir_admin
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
@exigir_admin
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
@exigir_admin
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

@app.route("/painel/login")
def pagina_login():
    return send_from_directory(PAINEL_DIR, "login.html")

@app.route("/painel")
def painel():
    if session.get("admin") is not True:
        return redirect(url_for("pagina_login"))

    return send_from_directory(PAINEL_DIR, "index.html")


# CARREGAR CSS, JAVASCRIPT E OUTROS ARQUIVOS DO PAINEL
@app.route("/painel/<path:arquivo>")
def arquivos_painel(arquivo):
    return send_from_directory(
        PAINEL_DIR,
        arquivo
    )


# LISTAR CADASTROS DE COMPUTADORES PENDENTES
@app.route("/api/cadastros/pendentes", methods=["GET"])
@exigir_admin
def listar_cadastros_pendentes():
    return jsonify({
        "cadastros": cadastros.listar_pendentes()
    })



# ==========================================
# CADASTRO SEGURO DE COMPUTADORES
# ==========================================

@app.route("/api/agente/cadastro", methods=["POST"])
def solicitar_cadastro_agente():
    dados = request.get_json(silent=True) or {}

    try:
        identificador = cadastros.solicitar(
            dados.get("nome"),
            dados.get("chave_publica")
        )
    except (ValueError, TypeError) as erro:
        return jsonify({"erro": str(erro)}), 400

    return jsonify({
        "mensagem": "Cadastro solicitado.",
        "identificador": identificador
    }), 201


@app.route(
    "/api/agente/cadastro/<identificador>/desafio",
    methods=["POST"]
)
def gerar_desafio_cadastro(identificador):
    cadastro = cadastros.pendentes.get(identificador)

    if not cadastro or cadastro["status"] != "pendente":
        return jsonify({
            "erro": "Cadastro pendente não encontrado."
        }), 404

    desafio = desafios.gerar(identificador)

    return jsonify({
        "desafio": desafio
    })


@app.route(
    "/api/agente/cadastro/<identificador>/verificar",
    methods=["POST"]
)
def verificar_identidade_agente(identificador):
    cadastro = cadastros.pendentes.get(identificador)

    if not cadastro or cadastro["status"] != "pendente":
        return jsonify({
            "erro": "Cadastro pendente não encontrado."
        }), 404

    dados = request.get_json(silent=True) or {}
    assinatura = dados.get("assinatura")

    if not isinstance(assinatura, str):
        return jsonify({
            "erro": "Assinatura inválida."
        }), 400

    try:
        valido = desafios.verificar(
            identificador,
            cadastro["chave_publica"],
            assinatura
        )
    except (ValueError, TypeError):
        valido = False

    if not valido:
        return jsonify({
            "erro": "Falha na verificação da identidade."
        }), 403

    cadastros.confirmar_identidade(identificador)

    return jsonify({
        "mensagem": "Identidade verificada."
    })


# ==========================================
# APROVAÇÃO ADMINISTRATIVA
# ==========================================

@app.route(
    "/api/cadastros/<identificador>/aprovar",
    methods=["POST"]
)
@exigir_admin
def aprovar_cadastro_agente(identificador):
    cadastro = cadastros.pendentes.get(identificador)

    if not cadastro or cadastro["status"] != "pendente":
        return jsonify({
            "erro": "Cadastro pendente não encontrado."
        }), 404

    if not cadastro.get("identidade_verificada", False):
        return jsonify({
            "erro": "Identidade ainda não verificada."
        }), 409

    # Impede aprovar novamente a mesma solicitação.
    cadastro_aprovado = cadastros.aprovar(identificador)

    if cadastro_aprovado is None:
        return jsonify({
            "erro": "Não foi possível aprovar o cadastro."
        }), 409

    dispositivo_id = dispositivos.cadastrar(
        cadastro_aprovado["nome"],
        cadastro_aprovado["chave_publica"]
    )

    # A ativação é realizada somente nesta rota administrativa.
    dispositivos.dispositivos[dispositivo_id]["ativo"] = True
    dispositivos.salvar()

    return jsonify({
        "mensagem": "Computador cadastrado e ativado.",
        "dispositivo_id": dispositivo_id
    })


@app.route(
    "/api/cadastros/<identificador>/recusar",
    methods=["POST"]
)
@exigir_admin
def recusar_cadastro_agente(identificador):
    if not cadastros.recusar(identificador):
        return jsonify({
            "erro": "Cadastro pendente não encontrado."
        }), 404

    return jsonify({
        "mensagem": "Cadastro recusado."
    })


# ==========================================
# AUTENTICAÇÃO DE DISPOSITIVOS CADASTRADOS
# ==========================================

@app.route(
    "/api/agente/autenticacao/desafio",
    methods=["POST"]
)
def desafio_autenticacao_agente():
    dados = request.get_json(silent=True) or {}
    identificador = dados.get("dispositivo_id")

    if not isinstance(identificador, str):
        return jsonify({
            "erro": "Identificador inválido."
        }), 400

    dispositivo = dispositivos.dispositivos.get(
        identificador
    )

    if not dispositivo or not dispositivo.get("ativo", False):
        return jsonify({
            "erro": "Dispositivo não autorizado."
        }), 403

    desafio = desafios.gerar(
        f"agente:{identificador}"
    )

    return jsonify({
        "desafio": desafio,
        "validade_segundos": 120
    })


@app.route(
    "/api/agente/autenticacao/verificar",
    methods=["POST"]
)
def verificar_autenticacao_agente():
    dados = request.get_json(silent=True) or {}

    identificador = dados.get("dispositivo_id")
    assinatura = dados.get("assinatura")

    if not isinstance(identificador, str):
        return jsonify({
            "erro": "Identificador inválido."
        }), 400

    if not isinstance(assinatura, str):
        return jsonify({
            "erro": "Assinatura inválida."
        }), 400

    dispositivo = dispositivos.dispositivos.get(
        identificador
    )

    if not dispositivo or not dispositivo.get("ativo", False):
        return jsonify({
            "erro": "Dispositivo não autorizado."
        }), 403

    valido = desafios.verificar(
        f"agente:{identificador}",
        dispositivo["chave_publica"],
        assinatura
    )

    if not valido:
        return jsonify({
            "erro": "Falha na autenticação."
        }), 403

    return jsonify({
        "autenticado": True,
        "dispositivo_id": identificador,
        "mensagem": "Identidade do dispositivo confirmada."
    })


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
