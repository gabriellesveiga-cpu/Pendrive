
import tkinter as tk
from solicitacoes import GerenciadorSolicitacoes


janela = tk.Tk()
janela.title("Teste - USB Security Lab")
janela.geometry("400x220")

gerenciador = GerenciadorSolicitacoes(janela)

tk.Label(
    janela,
    text="USB SECURITY LAB",
    font=("Arial", 17, "bold")
).pack(pady=25)

tk.Label(
    janela,
    text="Teste de solicitação de assistência"
).pack(pady=10)

tk.Button(
    janela,
    text="Simular solicitação",
    command=lambda: gerenciador.receber_solicitacao(
        "Computador de teste",
        "sessao-teste-123"
    )
).pack(pady=20)

janela.mainloop()
