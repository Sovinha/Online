let historicoAtual = 0;
let modoVisualizacao = true;

// 🔹 NÚMERO FIXO DO WHATSAPP (FORMATO: 55DDDNÚMERO)
const NUMERO_WHATSAPP = "558396300542"; // <-- TROQUE AQUI

async function abrirModal(id, visualizar) {
    historicoAtual = id;
    modoVisualizacao = visualizar;

    const r = await fetch(`/historico/detalhes/${id}`);
    const d = await r.json();

    const tbody = document.getElementById("modalBody");
    tbody.innerHTML = "";

    d.dados.forEach(i => {
        tbody.innerHTML += `
        <tr>
            <td>${i.motoboy}</td>
            <td>${i.entregas}</td>
            <td>${i.km_medio}</td>
            <td>
                <input type="number"
                       step="0.01"
                       class="form-control"
                       value="${i.valor_final}"
                       ${modoVisualizacao ? "disabled" : ""}
                       data-id="${i.id}">
            </td>
            <td>
                <input type="text"
                       class="form-control"
                       value="${i.motivo ?? ""}"
                       ${modoVisualizacao ? "disabled" : ""}
                       data-motivo="${i.id}">
            </td>
        </tr>`;
    });

    document.getElementById("btnSalvar").style.display =
        modoVisualizacao ? "none" : "inline-block";

    document.getElementById("btnWhatsapp").style.display =
        modoVisualizacao ? "inline-block" : "none";

    new bootstrap.Modal(
        document.getElementById("modalHistorico")
    ).show();
}

async function salvarEdicao() {
    const itens = [];

    document.querySelectorAll("[data-id]").forEach(i => {
        const id = i.dataset.id;
        const valor = i.value;
        const motivo = document.querySelector(
            `[data-motivo="${id}"]`
        ).value;

        itens.push({
            id: id,
            valor_final: valor,
            motivo: motivo
        });
    });

    const r = await fetch("/historico/editar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            id: historicoAtual,
            itens: itens
        })
    });

    if (r.ok) {
        location.reload();
    } else {
        alert("Erro ao salvar");
    }
}

function enviarWhatsapp() {
    let mensagem = `📋 *Relatório de Entregas*\n\n`;

    document.querySelectorAll("[data-id]").forEach(i => {
        const id = i.dataset.id;
        const valor = i.value;
        const motivo = document.querySelector(
            `[data-motivo="${id}"]`
        ).value;

        const linha = i.closest("tr");
        const motoboy = linha.children[0].innerText;
        const entregas = linha.children[1].innerText;
        const km = linha.children[2].innerText;

        mensagem +=
            `👤 *Motoboy:* ${motoboy}\n` +
            `📦 *Entregas:* ${entregas}\n` +
            `🛣️ *KM médio:* ${km}\n` +
            `💰 *Valor final:* R$ ${valor}\n` +
            (motivo ? `📝 *Motivo:* ${motivo}\n` : "") +
            `———————————————\n`;
    });

    const url =
        `https://wa.me/${NUMERO_WHATSAPP}?text=${encodeURIComponent(mensagem)}`;

    window.open(url, "_blank");
}
