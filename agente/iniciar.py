
import tkinter as tk
from tkinter import messagebox

from autorizacao import pendrive_autorizado
from solicitacoes import GerenciadorSolicitacoes


class USBLab:
    def __init__(self, janela):
        self.janela = janela
        self.janela.title("USB Security Lab")
        self.janela.geometry("420x260")
        self.janela.resizable(False, False)

        self.ativo = True

        tk.Label(
            janela,
            text="USB SECURITY LAB",
            font=("Arial", 18, "bold")
        ).pack(pady=20)

        self.status = tk.Label(
            janela,
            text="Verificando pendrive...",
            font=("Arial", 12)
        )
        self.status.pack(pady=15)

        self.detalhe = tk.Label(
            janela,
            text="Aguardando autorização",
            font=("Arial", 10)
        )
        self.detalhe.pack(pady=5)

        tk.Button(
            janela,
            text="Encerrar",
            command=self.encerrar
        ).pack(pady=20)

        # Gerenciador de solicitações
        self.gerenciador_solicitacoes = GerenciadorSolicitacoes(
            self.janela
        )

        self.gerenciador_solicitacoes.iniciar_monitoramento()

        self.verificar()

    def verificar(self):
        if not self.ativo:
            return

        try:
            autorizado = pendrive_autorizado()

            if autorizado:
                self.status.config(
                    text="PENDRIVE AUTORIZADO",
                    fg="green"
                )
                self.detalhe.config(
                    text="Chave física reconhecida."
                )
            else:
                self.status.config(
                    text="ACESSO BLOQUEADO",
                    fg="red"
                )
                self.detalhe.config(
                    text="Conecte o pendrive autorizado."
                )

        except Exception:
            self.status.config(
                text="ERRO NA VERIFICAÇÃO",
                fg="red"
            )

        self.janela.after(1000, self.verificar)

    def encerrar(self):
        self.ativo = False

        self.gerenciador_solicitacoes.monitoramento_ativo = False

        if self.gerenciador_solicitacoes.sessao_ativa:
            self.gerenciador_solicitacoes.encerrar_sessao()

        self.janela.destroy()


def iniciar():
    janela = tk.Tk()
    app = USBLab(janela)
    janela.mainloop()


if __name__ == "__main__":
    iniciar()
