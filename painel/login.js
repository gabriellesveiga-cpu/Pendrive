
const formulario = document.getElementById("loginForm");
const campoChave = document.getElementById("chave");
const botao = document.getElementById("entrar");
const mensagem = document.getElementById("mensagem");

formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();

    botao.disabled = true;
    mensagem.textContent = "Verificando credenciais...";

    try {
        const resposta = await fetch("/api/admin/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "same-origin",
            body: JSON.stringify({
                chave: campoChave.value
            })
        });

        if (!resposta.ok) {
            throw new Error("Chave administrativa inválida.");
        }

        campoChave.value = "";
        mensagem.textContent = "Login realizado!";

        window.location.replace("/painel");

    } catch (erro) {
        mensagem.textContent = erro.message;
    } finally {
        botao.disabled = false;
    }
});
