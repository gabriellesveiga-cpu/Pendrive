
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ARQUIVO_HISTORICO = BASE_DIR / "historico.json"


def registrar_atividade(tipo, descricao, detalhes=None):
    """
    Registra uma atividade sem guardar senhas
    ou conteúdo dos arquivos.
    """
    atividades = []

    if ARQUIVO_HISTORICO.exists():
        try:
            with ARQUIVO_HISTORICO.open(
                "r", encoding="utf-8"
            ) as arquivo:
                atividades = json.load(arquivo)

            if not isinstance(atividades, list):
                atividades = []

        except (json.JSONDecodeError, OSError):
            atividades = []

    atividade = {
        "data": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "tipo": str(tipo)[:50],
        "descricao": str(descricao)[:200],
        "detalhes": detalhes or {},
    }

    atividades.insert(0, atividade)

    # Mantém somente as 500 atividades mais recentes.
    atividades = atividades[:500]

    temporario = ARQUIVO_HISTORICO.with_suffix(".tmp")

    with temporario.open("w", encoding="utf-8") as arquivo:
        json.dump(
            atividades,
            arquivo,
            ensure_ascii=False,
            indent=2,
        )

    temporario.replace(ARQUIVO_HISTORICO)


def listar_atividades(limite=100):
    if not ARQUIVO_HISTORICO.exists():
        return []

    try:
        with ARQUIVO_HISTORICO.open(
            "r", encoding="utf-8"
        ) as arquivo:
            atividades = json.load(arquivo)

        if not isinstance(atividades, list):
            return []

        limite = max(1, min(int(limite), 500))
        return atividades[:limite]

    except (json.JSONDecodeError, OSError, ValueError):
        return []
