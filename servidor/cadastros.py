
import secrets
from datetime import datetime, timezone


class GerenciadorCadastros:
    def __init__(self):
        self.pendentes = {}

    def solicitar(self, nome, chave_publica):
        if not isinstance(nome, str) or not nome.strip():
            raise ValueError("Nome do computador inválido.")

        if not isinstance(chave_publica, str):
            raise ValueError("Chave pública inválida.")

        try:
            chave = bytes.fromhex(chave_publica)
        except ValueError:
            raise ValueError("Formato da chave pública inválido.")

        if len(chave) != 32:
            raise ValueError("A chave pública deve ter 32 bytes.")

        identificador = secrets.token_urlsafe(24)

       
        self.pendentes[identificador] = {
            "nome": nome.strip()[:100],
            "chave_publica": chave_publica.lower(),
            "criado_em": datetime.now(timezone.utc).isoformat(),
            "status": "pendente",
            "identidade_verificada": False
        }


        return identificador

    def listar_pendentes(self):
        return [
            {
                "identificador": identificador,
                "nome": dados["nome"],
                "criado_em": dados["criado_em"],
                "status": dados["status"],
                "identidade_verificada": dados.get(
                    "identidade_verificada", False
                )
            }
            for identificador, dados in self.pendentes.items()
            if dados["status"] == "pendente"
        ]


        
    def confirmar_identidade(self, identificador):
        cadastro = self.pendentes.get(identificador)

        if not cadastro:
            return False

        if cadastro["status"] != "pendente":
            return False

        cadastro["identidade_verificada"] = True

        return True


   
    def aprovar(self, identificador):
        cadastro = self.pendentes.get(identificador)

        if not cadastro or cadastro["status"] != "pendente":
            return None

        if not cadastro.get("identidade_verificada", False):
            return None

        cadastro["status"] = "aprovado"
        return cadastro


    def recusar(self, identificador):
        cadastro = self.pendentes.get(identificador)

        if not cadastro or cadastro["status"] != "pendente":
            return False

        cadastro["status"] = "recusado"
        return True
