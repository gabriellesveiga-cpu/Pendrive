
const pageTitles = {
    inicio: "Visão geral",
    protecao: "Proteção",
    usb: "Dispositivos USB",
    relatorios: "Relatórios",
    configuracoes: "Configurações"
};

const navigationButtons = document.querySelectorAll("[data-page]");
const pageTitle = document.getElementById("pageTitle");

const protecaoPage = document.getElementById("protecaoPage");
const analiseTool = document.getElementById("analiseTool");
const cofreTool = document.getElementById("cofreTool");

let ferramentaAtual = "inicio";

// NAVEGAÇÃO PRINCIPAL
function abrirPagina(page) {
    if (!pageTitles[page]) return;

    ferramentaAtual = page;
    pageTitle.textContent = pageTitles[page];

    document.querySelectorAll(".nav-item").forEach((item) => {
        item.classList.toggle("active", item.dataset.page === page);
    });

    if (protecaoPage) {
        protecaoPage.hidden = page !== "protecao";
    }

    if (analiseTool) analiseTool.hidden = true;
    if (cofreTool) cofreTool.hidden = true;

    document.querySelectorAll(
        ".main > .welcome, " +
        ".main > .section-heading, " +
        ".main > .cards, " +
        ".main > .lower-grid"
    ).forEach((secao) => {
        secao.hidden = page !== "inicio";
    });
}

navigationButtons.forEach((button) => {
    button.addEventListener("click", () => {
        abrirPagina(button.dataset.page);
    });
});

// NAVEGAÇÃO ENTRE AS FERRAMENTAS DE PROTEÇÃO
document.querySelectorAll("[data-tool]").forEach((button) => {
    button.addEventListener("click", () => {
        const tool = button.dataset.tool;

        if (tool === "voltar") {
            if (analiseTool) analiseTool.hidden = true;
            if (cofreTool) cofreTool.hidden = true;
            return;
        }

        if (ferramentaAtual !== "protecao") return;

        if (analiseTool) analiseTool.hidden = tool !== "analise";
        if (cofreTool) cofreTool.hidden = tool !== "cofre";
    });
});

// CONSULTA INFORMAÇÕES REAIS DO COMPUTADOR
async function atualizarComputador() {
    try {
        const resposta = await fetch("/api/status");

        if (!resposta.ok) {
            throw new Error("Não foi possível consultar o servidor.");
        }

        const dados = await resposta.json();

        const computerStatus = document.getElementById("computerStatus");

        if (computerStatus) {
            computerStatus.textContent = dados.computador;
        }

        const cards = document.querySelectorAll(".main > .cards > .card");

        if (cards[2]) {
            cards[2].querySelector("h3").textContent =
                `${dados.memoria_percentual}%`;

            cards[2].querySelector("p").textContent =
                "Uso da memória RAM";

            cards[2].querySelector("small").textContent =
                `${dados.memoria_total_gb} GB de memória total`;
        }

        if (cards[3]) {
            cards[3].querySelector("h3").textContent =
                `${dados.disco_livre_gb} GB livres`;

            cards[3].querySelector("p").textContent =
                "Armazenamento C:";

            cards[3].querySelector("small").textContent =
                `${dados.disco_percentual}% do disco utilizado`;
        }
    } catch (erro) {
        console.error("Erro ao consultar o computador:", erro);

        const computerStatus = document.getElementById("computerStatus");

        if (computerStatus) {
            computerStatus.textContent = "Servidor indisponível";
        }
    }
}

atualizarComputador();
setInterval(atualizarComputador, 5000);

// AUXILIAR PARA LER ERROS DO SERVIDOR
async function lerErro(resposta, mensagemPadrao) {
    try {
        const dados = await resposta.json();
        return dados.erro || mensagemPadrao;
    } catch {
        return mensagemPadrao;
    }
}

// AUXILIAR PARA BAIXAR UM ARQUIVO
function baixarArquivo(blob, nomeArquivo) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = nomeArquivo;
    document.body.appendChild(link);
    link.click();
    link.remove();

    setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// ANÁLISE DE ARQUIVOS
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
                hash.textContent =
                    `SHA-256: ${item.sha256 || "Não calculado"}`;

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

// CRIAR COFRE CRIPTOGRAFADO
const vaultCreateForm = document.getElementById("vaultCreateForm");

if (vaultCreateForm) {
    vaultCreateForm.addEventListener("submit", async (evento) => {
        evento.preventDefault();

        const campoArquivos = document.getElementById("vaultFiles");
        const campoSenha = document.getElementById("vaultCreatePassword");
        const botao = document.getElementById("vaultCreateButton");
        const mensagem = document.getElementById("vaultCreateMessage");

        if (!campoArquivos.files.length) {
            mensagem.textContent = "Selecione os arquivos do projeto.";
            return;
        }

        if (campoSenha.value.length < 12) {
            mensagem.textContent =
                "A senha precisa ter pelo menos 12 caracteres.";
            return;
        }

        const dadosFormulario = new FormData();

        for (const arquivo of campoArquivos.files) {
            dadosFormulario.append("arquivos", arquivo);
        }

        dadosFormulario.append("senha", campoSenha.value);

        botao.disabled = true;
        botao.textContent = "Criptografando...";
        mensagem.textContent = "Criando o cofre com segurança...";

        try {
            const resposta = await fetch("/api/cofre/criar", {
                method: "POST",
                body: dadosFormulario
            });

            if (!resposta.ok) {
                throw new Error(
                    await lerErro(resposta, "Não foi possível criar o cofre.")
                );
            }

            const arquivoCofre = await resposta.blob();

            baixarArquivo(arquivoCofre, "meu_cofre.usblab");

            mensagem.textContent =
                "Cofre criado! Guarde o arquivo .usblab em um local seguro.";

            vaultCreateForm.reset();
        } catch (erro) {
            console.error("Erro ao criar cofre:", erro);
            mensagem.textContent = erro.message;
        } finally {
            botao.disabled = false;
            botao.textContent = "Criar cofre criptografado";
        }
    });
}

// ABRIR COFRE EXISTENTE
const vaultOpenForm = document.getElementById("vaultOpenForm");

if (vaultOpenForm) {
    vaultOpenForm.addEventListener("submit", async (evento) => {
        evento.preventDefault();

        const campoArquivo = document.getElementById("vaultFile");
        const campoSenha = document.getElementById("vaultOpenPassword");
        const botao = document.getElementById("vaultOpenButton");
        const mensagem = document.getElementById("vaultOpenMessage");

        if (!campoArquivo.files.length) {
            mensagem.textContent = "Selecione um arquivo .usblab.";
            return;
        }

        if (!campoSenha.value) {
            mensagem.textContent = "Informe a senha do cofre.";
            return;
        }

        const dadosFormulario = new FormData();

        dadosFormulario.append("cofre", campoArquivo.files[0]);
        dadosFormulario.append("senha", campoSenha.value);

        botao.disabled = true;
        botao.textContent = "Abrindo cofre...";
        mensagem.textContent = "Verificando senha e descriptografando...";

        try {
            const resposta = await fetch("/api/cofre/abrir", {
                method: "POST",
                body: dadosFormulario
            });

            if (!resposta.ok) {
                throw new Error(
                    await lerErro(resposta, "Não foi possível abrir o cofre.")
                );
            }

            const arquivoZip = await resposta.blob();

            baixarArquivo(arquivoZip, "projetos_recuperados.zip");

            mensagem.textContent =
                "Cofre aberto! Os arquivos foram baixados em um ZIP.";

            vaultOpenForm.reset();
        } catch (erro) {
            console.error("Erro ao abrir cofre:", erro);
            mensagem.textContent = erro.message;
        } finally {
            botao.disabled = false;
            botao.textContent = "Descriptografar arquivos";
        }
    });
}

// INICIA NA VISÃO GERAL
abrirPagina("inicio");
