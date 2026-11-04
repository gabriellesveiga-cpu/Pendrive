
import tkinter as tk
from tkinter import messagebox

from autorizacao import pendrive_autorizado
from solicitacoes import GerenciadorSolicitacoes
from identidade import preparar_identidade


class USBLab:
    def __init__(self, janela):
        self.janela = janela
        self.janela.title("USB Security Lab")
        self.janela.geometry("460x380")
        self.janela.resizable(False, False)

        self.ativo = True
        self.chave_publica = None

        try:
            self.chave_publica = preparar_identidade()
        except Exception as erro:
            messagebox.showerror(
                "Erro na identidade",
                f"Não foi possível preparar a identidade:\n{erro}"
            )

        tk.Label(
            janela,
            text="USB SECURITY LAB",
            font=("Arial", 19, "bold")
        ).pack(pady=18)

        self.status = tk.Label(
            janela,
            text="Verificando pendrive...",
            font=("Arial", 12, "bold")
        )
        self.status.pack(pady=10)

        self.detalhe = tk.Label(
            janela,
            text="Aguardando autorização",
            font=("Arial", 10)
        )
        self.detalhe.pack(pady=5)

        self.status_sessao = tk.Label(
            janela,
            text="Nenhuma sessão autorizada",
            font=("Arial", 11),
            fg="gray"
        )
        self.status_sessao.pack(pady=15)

        tk.Button(
            janela,
            text="Encerrar sessão",
            command=self.encerrar_sessao,
            width=22
        ).pack(pady=5)

        tk.Button(
            janela,
            text="Fechar programa",
            command=self.encerrar,
            width=22
        ).pack(pady=5)

        self.gerenciador_solicitacoes = GerenciadorSolicitacoes(
            self.janela
        )

        self.gerenciador_solicitacoes.iniciar_monitoramento()

        self.janela.protocol(
            "WM_DELETE_WINDOW",
            self.encerrar
        )

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

                if self.gerenciador_solicitacoes.sessao_ativa:
                    self.gerenciador_solicitacoes.encerrar_sessao()

            if self.gerenciador_solicitacoes.sessao_ativa:
                self.status_sessao.config(
                    text="Sessão autorizada",
                    fg="green"
                )
            else:
                self.status_sessao.config(
                    text="Nenhuma sessão autorizada",
                    fg="gray"
                )

        except Exception as erro:
            self.status.config(
                text="ERRO NA VERIFICAÇÃO",
                fg="red"
            )
            print("Erro:", erro)

        self.janela.after(1000, self.verificar)

    def encerrar_sessao(self):
        self.gerenciador_solicitacoes.encerrar_sessao()

        self.status_sessao.config(
            text="Sessão encerrada",
            fg="red"
        )

    def encerrar(self):
        self.ativo = False

        self.gerenciador_solicitacoes.monitoramento_ativo = False
        self.gerenciador_solicitacoes.encerrar_sessao()

        self.janela.destroy()


def iniciar():
    janela = tk.Tk()
    USBLab(janela)
    janela.mainloop()


if __name__ == "__main__":
    iniciar()
