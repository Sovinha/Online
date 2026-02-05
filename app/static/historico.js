let historicoAtual = 0;
let dadosCompletosCachorro = null;
const NUMERO_WHATSAPP = "558396300542";

async function abrirModal(id, visualizar) {
    historicoAtual = id;
    const r = await fetch(`/historico/detalhes/${id}`);
    const d = await r.json();
    dadosCompletosCachorro = d; 

    const tbody = document.getElementById("modalBody");
    tbody.innerHTML = d.dados.map(i => `
        <tr>
            <td class="text-start">${i.motoboy}</td>
            <td>${i.entregas} <button class="btn btn-sm" onclick="toggleEntregas(${i.id})">🔍</button></td>
            <td>${i.km_medio} km</td>
            <td><input type="number" class="form-control form-control-sm mx-auto" style="width: 80px;" value="${i.valor_final}" ${visualizar ? "disabled" : ""} data-id="${i.id}"></td>
            <td><input type="text" class="form-control form-control-sm" value="${i.motivo ?? ""}" ${visualizar ? "disabled" : ""} data-motivo="${i.id}"></td>
        </tr>
        <tr id="detalhe-entrega-${i.id}" style="display: none;"><td colspan="5" class="bg-light text-start small p-3">IDs: ${i.pedidos}</td></tr>
    `).join('');

    document.getElementById("btnSalvar").style.display = visualizar ? "none" : "inline-block";
    document.getElementById("btnWhatsapp").style.display = visualizar ? "inline-block" : "none";
    new bootstrap.Modal(document.getElementById("modalHistorico")).show();
}

function toggleEntregas(id) {
    const el = document.getElementById(`detalhe-entrega-${id}`);
    el.style.display = el.style.display === "none" ? "table-row" : "none";
}

function enviarWhatsapp() {
    const d = dadosCompletosCachorro;
    let msg = `*RELATÓRIO - ${d.loja.toUpperCase()}*\nFaturamento: R$ ${d.faturamento}\nCobertura: ${d.cobertura}%\n\n`;
    document.querySelectorAll("[data-id]").forEach(i => {
        const motoboy = i.closest("tr").children[0].innerText;
        msg += `• *${motoboy}*: R$ ${i.value}\n`;
    });
    window.open(`https://wa.me/${NUMERO_WHATSAPP}?text=${encodeURIComponent(msg)}`, "_blank");
}

async function salvarEdicao() {
    const editados = Array.from(document.querySelectorAll("[data-id]")).map(i => ({
        id: i.dataset.id, valor: i.value, motivo: document.querySelector(`[data-motivo="${i.dataset.id}"]`).value
    }));
    const r = await fetch("/historico/editar", { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({dados: editados})});
    if (r.ok) location.reload();
}

async function excluirRegistro(id) {
    if (confirm("Excluir permanentemente?")) {
        const r = await fetch(`/historico/excluir/${id}`, { method: 'POST' });
        if (r.ok) location.reload();
    }
}