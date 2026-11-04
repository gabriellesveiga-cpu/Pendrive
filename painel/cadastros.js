
const listaCadastros = document.getElementById("listaCadastros");
const atualizarCadastros = document.getElementById("atualizarCadastros");

function mensagemCadastro(mensagem) {
    listaCadastros.replaceChildren();

    const linha = document.createElement("tr");
    const celula = document.createElement("td");

    celula.colSpan = 5;
    celula.textContent = mensagem;

    linha.appendChild(celula);
    listaCadastros.appendChild(linha);
}

async function respostaJSON(resposta) {
    const dados = await resposta.json();

    if (!resposta.ok) {
        throw new Error(dados.erro || `Erro HTTP ${resposta.status}`);
    }

    return dados;
}

async function obterCSRF() {
    const resposta = await fetch("/api/admin/csrf", {
        credentials: "same-origin"
    });

    const dados = await respostaJSON(resposta);

    // Compatibilidade com o campo retornado pelo login administrativo.
    const token = dados.csrf || dados.token || dados.csrf_token;

    if (!token) {
        throw new Error("Token CSRF não encontrado.");
    }

    return token;
}

async function alterarCadastro(identificador, acao) {
    const verbo = acao === "aprovar" ? "aprovar" : "recusar";

    if (!confirm(`Deseja ${verbo} este computador?`)) {
        return;
    }

    try {
        const csrf = await obterCSRF();

        const resposta = await fetch(
            `/api/cadastros/${encodeURIComponent(identificador)}/${acao}`,
            {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "X-CSRF-Token": csrf
                }
            }
        );

        const dados = await respostaJSON(resposta);

        alert(dados.mensagem || "Operação concluída.");
        await carregarCadastros();

    } catch (erro) {
        alert(`Erro: ${erro.message}`);
    }
}

async function carregarCadastros() {
    mensagemCadastro("Carregando cadastros...");

    try {
        const resposta = await fetch("/api/cadastros/pendentes", {
            credentials: "same-origin"
        });

        const dados = await respostaJSON(resposta);
        const cadastros = dados.cadastros || [];

        listaCadastros.replaceChildren();

        if (cadastros.length === 0) {
            mensagemCadastro("Nenhum cadastro pendente.");
            return;
        }

        for (const cadastro of cadastros) {
            const linha = document.createElement("tr");

            const nome = document.createElement("td");
            nome.textContent = cadastro.nome;

            const identificador = document.createElement("td");
            identificador.textContent = cadastro.identificador;

            const data = document.createElement("td");
            data.textContent = new Date(
                cadastro.criado_em
            ).toLocaleString("pt-BR");

            const identidade = document.createElement("td");
            identidade.textContent = cadastro.identidade_verificada
                ? "Verificada"
                : "Não verificada";

            const acoes = document.createElement("td");

            const aprovar = document.createElement("button");
            aprovar.type = "button";
            aprovar.textContent = "Aprovar";
            aprovar.disabled = !cadastro.identidade_verificada;

            aprovar.addEventListener("click", () => {
                alterarCadastro(cadastro.identificador, "aprovar");
            });

            const recusar = document.createElement("button");
            recusar.type = "button";
            recusar.textContent = "Recusar";

            recusar.addEventListener("click", () => {
                alterarCadastro(cadastro.identificador, "recusar");
            });

            acoes.append(aprovar, recusar);

            linha.append(
                nome,
                identificador,
                data,
                identidade,
                acoes
            );

            listaCadastros.appendChild(linha);
        }

    } catch (erro) {
        mensagemCadastro(`Erro ao carregar cadastros: ${erro.message}`);
    }
}

atualizarCadastros.addEventListener("click", carregarCadastros);

carregarCadastros();

