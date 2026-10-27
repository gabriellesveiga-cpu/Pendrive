
const pageTitles = {
    inicio: "Visão geral",
    protecao: "Proteção",
    usb: "Dispositivos USB",
    relatorios: "Relatórios",
    configuracoes: "Configurações"
};

const navigationButtons = document.querySelectorAll("[data-page]");
const pageTitle = document.getElementById("pageTitle");

function abrirPagina(page) {
    if (!pageTitles[page]) return;

    pageTitle.textContent = pageTitles[page];

    document.querySelectorAll(".nav-item").forEach((item) => {
        item.classList.toggle("active", item.dataset.page === page);
    });

    // Mostra a tela de proteção apenas quando ela for selecionada.
    const protecaoPage = document.getElementById("protecaoPage");

    if (protecaoPage) {
        protecaoPage.hidden = page !== "protecao";
    }

    // Esconde as seções da visão geral quando outra página é aberta.
    document.querySelectorAll(
        ".main > .welcome, .main > .section-heading, .main > .cards, .main > .lower-grid"
    ).forEach((secao) => {
        secao.hidden = page !== "inicio";
    });
}

navigationButtons.forEach((button) => {
    button.addEventListener("click", () => {
        abrirPagina(button.dataset.page);
    });
});

// Consulta informações reais do computador.
async function atualizarComputador() {
    try {
        const resposta = await fetch("/api/status");

        if (!resposta.ok) {
            throw new Error("Não foi possível consultar o servidor.");
        }

        const dados = await resposta.json();

        document.getElementById("computerStatus").textContent =
            dados.computador;

        const cards = document.querySelectorAll(".card");

        cards[2].querySelector("h3").textContent =
            `${dados.memoria_percentual}%`;
        cards[2].querySelector("p").textContent =
            "Uso da memória RAM";
        cards[2].querySelector("small").textContent =
            `${dados.memoria_total_gb} GB de memória total`;

        cards[3].querySelector("h3").textContent =
            `${dados.disco_livre_gb} GB livres`;
        cards[3].querySelector("p").textContent =
            "Armazenamento C:";
        cards[3].querySelector("small").textContent =
            `${dados.disco_percentual}% do disco utilizado`;

    } catch (erro) {
        console.error("Erro ao consultar o computador:", erro);

        document.getElementById("computerStatus").textContent =
            "Servidor indisponível";
    }
}

atualizarComputador();
setInterval(atualizarComputador, 5000);

// Análise inicial dos arquivos selecionados.
const scanForm = document.getElementById("scanForm");

if (scanForm) {
    scanForm.addEventListener("submit", async (evento) => {
        evento.preventDefault();

        const campoArquivos = document.getElementById("scanFiles");
        const botao = document.getElementById("scanButton");
        const resultados = document.getElementById("scanResults");

        if (!campoArquivos.files.length) {
            resultados.textContent = "Selecione pelo menos um arquivo.";
            return;
        }

        const dadosFormulario = new FormData();

        for (const arquivo of campoArquivos.files) {
            dadosFormulario.append("arquivos", arquivo);
        }

        botao.disabled = true;
        botao.textContent = "Analisando...";
        resultados.textContent = "A análise está em andamento...";

        try {
            const resposta = await fetch("/api/analisar", {
                method: "POST",
                body: dadosFormulario
            });

            const dados = await resposta.json();

            if (!resposta.ok) {
                throw new Error(dados.erro || "Falha na análise.");
            }

            resultados.replaceChildren();

            const resumo = document.createElement("p");
            resumo.textContent =
                `Análise inicial concluída. Arquivos verificados: ${dados.total}.`;
            resultados.appendChild(resumo);

            for (const item of dados.resultados) {
                const cartao = document.createElement("article");
                cartao.className = "scan-result";

                const nome = document.createElement("h3");
                nome.textContent = item.nome;

                const situacao = document.createElement("p");
                situacao.textContent = `Situação: ${item.situacao}`;

                const detalhe = document.createElement("p");
                detalhe.textContent = item.detalhe;

                const tamanho = document.createElement("p");
                tamanho.textContent =
                    `Tamanho: ${item.tamanho_bytes ?? 0} bytes`;

                const hash = document.createElement("p");
                hash.textContent = `SHA-256: ${item.sha256 || "Não calculado"}`;

                cartao.append(nome, situacao, detalhe, tamanho, hash);
                resultados.appendChild(cartao);
            }

        } catch (erro) {
            console.error("Erro na análise:", erro);
            resultados.textContent =
                `Não foi possível analisar os arquivos: ${erro.message}`;
        } finally {
            botao.disabled = false;
            botao.textContent = "Analisar arquivos";
        }
    });
}
