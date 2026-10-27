
const pageTitles = {
    inicio: "Visão geral",
    protecao: "Proteção",
    usb: "Dispositivos USB",
    relatorios: "Relatórios",
    configuracoes: "Configurações"
};

const navigationButtons = document.querySelectorAll("[data-page]");
const pageTitle = document.getElementById("pageTitle");

navigationButtons.forEach((button) => {
    button.addEventListener("click", () => {
        const page = button.dataset.page;

        if (!pageTitles[page]) return;

        pageTitle.textContent = pageTitles[page];

        document.querySelectorAll(".nav-item").forEach((item) => {
            item.classList.toggle(
                "active",
                item.dataset.page === page
            );
        });
    });
});

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

        // Cartão 3: uso da memória RAM
        cards[2].querySelector("h3").textContent =
            `${dados.memoria_percentual}%`;

        cards[2].querySelector("p").textContent = "Uso da memória RAM";

        cards[2].querySelector("small").textContent =
            `${dados.memoria_total_gb} GB de memória total`;

        // Cartão 4: armazenamento
        cards[3].querySelector("h3").textContent =
            `${dados.disco_livre_gb} GB livres`;

        cards[3].querySelector("p").textContent =
            "Armazenamento C:";

        cards[3].querySelector("small").textContent =
            `${dados.disco_percentual}% do disco utilizado`;

        console.log("Informações do computador atualizadas.", dados);

    } catch (erro) {
        console.error("Erro ao consultar o computador:", erro);
        document.getElementById("computerStatus").textContent =
            "Servidor indisponível";
    }
}

atualizarComputador();
setInterval(atualizarComputador, 5000);
