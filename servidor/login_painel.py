
import hmac
import secrets
from pathlib import Path

from flask import Blueprint, jsonify, request, session

login_painel = Blueprint("login_painel", __name__)

ARQUIVO_CHAVE = Path.home() / ".usb_security_lab_admin"


@login_painel.route("/api/admin/login", methods=["POST"])
def entrar():
    dados = request.get_json(silent=True) or {}
    chave_informada = dados.get("chave", "")

    if not isinstance(chave_informada, str):
        return jsonify({"erro": "Credencial inválida."}), 400

    if not ARQUIVO_CHAVE.is_file():
        return jsonify({"erro": "Login indisponível."}), 503

    chave_correta = ARQUIVO_CHAVE.read_text(
        encoding="utf-8"
    ).strip()

    if not chave_correta or not hmac.compare_digest(
        chave_informada, chave_correta
    ):
        return jsonify({"erro": "Credencial inválida."}), 401

    session.clear()
    session["admin"] = True
    session["csrf"] = secrets.token_urlsafe(32)

    return jsonify({
        "mensagem": "Login realizado.",
        "csrf": session["csrf"]
    })


@login_painel.route("/api/admin/logout", methods=["POST"])
def sair():
    session.clear()
    return jsonify({"mensagem": "Sessão encerrada."})


@login_painel.route("/api/admin/status", methods=["GET"])
def status_login():
    return jsonify({
        "autenticado": session.get("admin") is True
    })


@login_painel.route("/api/admin/csrf", methods=["GET"])
def obter_csrf():
    if session.get("admin") is not True:
        return jsonify({
            "erro": "Login necessário."
        }), 401

    token = session.get("csrf")

    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf"] = token

    resposta = jsonify({"csrf": token})
    resposta.headers["Cache-Control"] = "no-store"

    return resposta
