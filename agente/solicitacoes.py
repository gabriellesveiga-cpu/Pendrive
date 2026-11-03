import tkinter as tk
from tkinter import messagebox

import requests

from autorizacao import pendrive_autorizado


SERVIDOR = "http://127.0.0.1:5000"


class GerenciadorSolicitacoes:
    def __init__(self, janela):
        self.janela = janela

        self.sessao_ativa = False
        self.identificador_ativo = None

        self.janela_solicitacao = None
        self.identificador_pendente = None

        self.solicitacoes_processadas = set()
        self.monitoramento_ativo = False

    def iniciar_monitoramento(self):
        if self.monitoramento_ativo:
            return

        self.monitoramento_ativo = True
        self.verificar_solicitacoes()

    def verificar_solicitacoes(self):
        if not self.monitoramento_ativo:
            return

        try:
            autorizado = pendrive_autorizado()

            # Se o pendrive for removido, encerra a sessão ativa.
            if not autorizado:
                if self.sessao_ativa:
                    self.encerrar_sessao()

            else:
                resposta = requests.get(
                    f"{SERVIDOR}/solicitacoes/pendentes",
                    timeout=2
                )

                resposta.raise_for_status()

                solicitacoes = resposta.json().get(
                    "solicitacoes", []
                )

                if self.janela_solicitacao is None and not self.sessao_ativa:
                    for solicitacao in solicitacoes:
                        identificador = solicitacao["identificador"]

                        if identificador not in self.solicitacoes_processadas:
                            print("TENTANDO ABRIR JANELA...")
                            self.receber_solicitacao(
                                solicitacao["nome"],
                                identificador
                            )
                            print("SOLICITAÇÃO ENCONTRADA:", identificador)
                            break

        except requests.RequestException as erro:
            print("Erro ao consultar servidor:", erro)

        except Exception as erro:
            print("Erro no monitoramento:", erro)

        self.janela.after(2000, self.verificar_solicitacoes)

    def receber_solicitacao(self, nome_computador, identificador):
        if self.janela_solicitacao is not None:
            return

        self.identificador_pendente = identificador

        tela = tk.Toplevel(self.janela)
        self.janela_solicitacao = tela

        tela.title("Solicitação de assistência")
        tela.geometry("380x240")
        tela.resizable(False, False)
        tela.transient(self.janela)
        tela.grab_set()

        tk.Label(
            tela,
            text="SOLICITAÇÃO DE ASSISTÊNCIA",
            font=("Arial", 13, "bold")
        ).pack(pady=20)

        tk.Label(
            tela,
            text=f"Computador solicitante:\n{nome_computador}",
            font=("Arial", 11)
        ).pack(pady=10)

        tk.Label(
            tela,
            text="Deseja permitir esta sessão?",
            font=("Arial", 10)
        ).pack(pady=5)

        botoes = tk.Frame(tela)
        botoes.pack(pady=15)

        tk.Button(
            botoes,
            text="Recusar",
            command=self.recusar,
            width=12
        ).pack(side="left", padx=8)

        tk.Button(
            botoes,
            text="Aprovar",
            command=self.aprovar,
            width=12
        ).pack(side="left", padx=8)

        tela.protocol("WM_DELETE_WINDOW", self.recusar)

    def aprovar(self):
        identificador = self.identificador_pendente

        if not identificador:
            return

        try:
            # Confere novamente se o pendrive está autorizado.
            if not pendrive_autorizado():
                messagebox.showwarning(
                    "USB Security Lab",
                    "O pendrive autorizado não foi encontrado."
                )
                self.recusar()
                return

            resposta = requests.post(
                f"{SERVIDOR}/sessao/{identificador}/aprovar",
                timeout=3
            )

            resposta.raise_for_status()

            self.sessao_ativa = True
            self.identificador_ativo = identificador
            self.solicitacoes_processadas.add(identificador)

            self.fechar_janela()

            messagebox.showinfo(
                "USB Security Lab",
                "Solicitação aprovada."
            )

            print("Sessão aprovada:", identificador)

        except requests.RequestException as erro:
            messagebox.showerror(
                "Erro",
                f"Não foi possível aprovar a solicitação:\n{erro}"
            )

    def recusar(self):
        identificador = self.identificador_pendente

        if identificador:
            try:
                requests.post(
                    f"{SERVIDOR}/sessao/{identificador}/recusar",
                    timeout=3
                ).raise_for_status()

                self.solicitacoes_processadas.add(identificador)

            except requests.RequestException as erro:
                print("Erro ao recusar solicitação:", erro)

        self.fechar_janela()
        print("Solicitação recusada.")

    def fechar_janela(self):
        if self.janela_solicitacao:
            self.janela_solicitacao.grab_release()
            self.janela_solicitacao.destroy()
            self.janela_solicitacao = None

        self.identificador_pendente = None

    def encerrar_sessao(self):
        identificador = self.identificador_ativo

        if identificador:
            try:
                requests.post(
                    f"{SERVIDOR}/sessao/{identificador}/encerrar",
                    timeout=3
                ).raise_for_status()

            except requests.RequestException as erro:
                print("Erro ao comunicar encerramento:", erro)

        self.sessao_ativa = False
        self.identificador_ativo = None

        print("Sessão encerrada.")