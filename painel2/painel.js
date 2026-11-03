
const API = "";

const totalSessoes = document.getElementById("totalSessoes");
const pendentes = document.getElementById("pendentes");
const ativas = document.getElementById("ativas");
const encerradas = document.getElementById("encerradas");
const statusServidor = document.getElementById("statusServidor");
const listaSessoes = document.getElementById("listaSessoes");
const botaoAtualizar = document.getElementById("atualizar");

function criarCelula(texto) {
    const td = document.createElement("td");
    td.textContent = texto ?? "—";
    return td;
}

function formatarData(data) {
    if (!data) return "—";

    const dataObj = new Date(data);

    if (Number.isNaN(dataObj.getTime())) return data;

    return dataObj.toLocaleString("pt-BR");
}

function nomeStatus(status) {
    const nomes = {
        aguardando_aprovacao: "Aguardando aprovação",
        aprovada: "Aprovada",
        ativa: "Ativa",
        recusada: "Recusada",
        encerrada: "Encerrada"
    };

    return nomes[status] || status || "Desconhecido";
}

function classeStatus(status) {
    if (status === "aguardando_aprovacao") return "status-pendente";
    if (status === "aprovada" || status === "ativa") return "status-aprovada";
    if (status === "recusada") return "status-recusada";
    return "status-encerrada";
}

async function verificarServidor() {
    try {
        const resposta = await fetch(`${API}/status`);

        if (!resposta.ok) throw new Error("Servidor indisponível");

        statusServidor.textContent = "Servidor conectado";
        statusServidor.style.color = "#65dba5";
    } catch (erro) {
        statusServidor.textContent = "Servidor desconectado";
        statusServidor.style.color = "#e69ba8";
    }
}

function adicionarLinha(sessao) {
    const linha = document.createElement("tr");

    linha.appendChild(criarCelula(sessao.nome));
    linha.appendChild(criarCelula(sessao.identificador));
    linha.appendChild(criarCelula(formatarData(sessao.criada_em)));

    const celulaStatus = document.createElement("td");
    const etiqueta = document.createElement("span");

    etiqueta.className = `status ${classeStatus(sessao.status)}`;
    etiqueta.textContent = nomeStatus(sessao.status);

    celulaStatus.appendChild(etiqueta);
    linha.appendChild(celulaStatus);

    const celulaAcao = document.createElement("td");

    if (sessao.status === "aprovada" || sessao.status === "ativa") {
        const botao = document.createElement("button");

        botao.textContent = "Encerrar";
        botao.className = "encerrar";

        botao.addEventListener("click", () => {
            encerrarSessao(sessao.identificador);
        });

        celulaAcao.appendChild(botao);
    } else {
        celulaAcao.textContent = "—";
    }

    linha.appendChild(celulaAcao);
    listaSessoes.appendChild(linha);
}

async function carregarSessoes() {
    try {
        const resposta = await fetch(`${API}/sessoes`);

        if (!resposta.ok) {
            throw new Error("Não foi possível carregar as sessões.");
        }

        const dados = await resposta.json();

        const sessoes = Array.isArray(dados)
            ? dados
            : dados.sessoes || [];

        totalSessoes.textContent = sessoes.length;

        pendentes.textContent = sessoes.filter(
            s => s.status === "aguardando_aprovacao"
        ).length;

        ativas.textContent = sessoes.filter(
            s => s.status === "aprovada" || s.status === "ativa"
        ).length;

        encerradas.textContent = sessoes.filter(
            s => s.status === "encerrada" || s.status === "recusada"
        ).length;

        listaSessoes.replaceChildren();

        if (sessoes.length === 0) {
            const linha = document.createElement("tr");
            const celula = criarCelula("Nenhuma sessão registrada.");
            celula.colSpan = 5;
            linha.appendChild(celula);
            listaSessoes.appendChild(linha);
            return;
        }

        sessoes.forEach(adicionarLinha);

    } catch (erro) {
        console.error(erro);

        listaSessoes.replaceChildren();

        const linha = document.createElement("tr");
        const celula = criarCelula("Não foi possível carregar as sessões.");
        celula.colSpan = 5;
        linha.appendChild(celula);
        listaSessoes.appendChild(linha);
    }
}

async function encerrarSessao(identificador) {
    const confirmar = window.confirm(
        "Tem certeza de que deseja encerrar esta sessão?"
    );

    if (!confirmar) return;

    try {
        const resposta = await fetch(
            `${API}/sessao/${encodeURIComponent(identificador)}/encerrar`,
            { method: "POST" }
        );

        if (!resposta.ok) {
            throw new Error("Não foi possível encerrar a sessão.");
        }

        await atualizarPainel();

        alert("Sessão encerrada.");

    } catch (erro) {
        alert(erro.message);
    }
}

async function atualizarPainel() {
    await verificarServidor();
    await carregarSessoes();
}

botaoAtualizar.addEventListener("click", atualizarPainel);

atualizarPainel();
setInterval(atualizarPainel, 5000);

