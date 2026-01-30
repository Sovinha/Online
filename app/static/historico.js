let historicoAtual = 0;
let modoVisualizacao = true;
let dadosCompletosCachorro = null; // 🔹 Variável para guardar os dados financeiros do registro

const NUMERO_WHATSAPP = "558396300542";

async function abrirModal(id, visualizar) {
    historicoAtual = id;
    modoVisualizacao = visualizar;

    const r = await fetch(`/historico/detalhes/${id}`);
    const d = await r.json();
    dadosCompletosCachorro = d; // 🔹 Salva o JSON completo (com faturamento, taxas, etc)

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

    document.getElementById("btnSalvar").style.display = modoVisualizacao ? "none" : "inline-block";
    document.getElementById("btnWhatsapp").style.display = modoVisualizacao ? "inline-block" : "none";

    new bootstrap.Modal(document.getElementById("modalHistorico")).show();
}

function enviarWhatsapp() {
    if (!dadosCompletosCachorro) return;

    const d = dadosCompletosCachorro;
    
    // 🔹 Cabeçalho com Informações da Loja e Financeiro
    let mensagem = `*RELATÓRIO DE ENTREGAS - ${d.loja}*\n`;
    mensagem += `*Data:* ${d.data}\n`;
    mensagem += `*Turno:* ${d.turno}\n\n`;
    
    mensagem += `*FINANCEIRO GERAL:*\n`;
    mensagem += `━━━━━━━━━━━━━━━━━━━━\n`;
    mensagem += `*FATURAMENTO TOTAL:* R$ ${d.faturamento.toLocaleString('pt-BR', {minimumFractionDigits: 2})}\n`;
    mensagem += `*TAXAS (CLIENTES):* R$ ${d.taxas_clientes.toLocaleString('pt-BR', {minimumFractionDigits: 2})}\n`;
    mensagem += `*PAGO MOTOBOYS:* R$ ${d.pago_motoboys.toLocaleString('pt-BR', {minimumFractionDigits: 2})}\n`;
    mensagem += `*COBERTURA DE FRETE:* ${d.cobertura}%\n`;
    mensagem += `━━━━━━━━━━━━━━━━━━━━\n\n`;

    mensagem += `*DETALHE POR MOTOBOY:*\n`;

    // 🔹 Percorre os motoboys para listar na mensagem
    document.querySelectorAll("[data-id]").forEach(i => {
        const id = i.dataset.id;
        const valor = parseFloat(i.value).toLocaleString('pt-BR', {minimumFractionDigits: 2});
        const motivo = document.querySelector(`[data-motivo="${id}"]`).value;

        const linha = i.closest("tr");
        const motoboy = linha.children[0].innerText;
        const entregas = linha.children[1].innerText;

        mensagem += `• *${motoboy}:* R$ ${valor} (${entregas} entr.)${motivo ? ` _Motivo: ${motivo}_` : ""}\n`;
    });

    const url = `https://wa.me/${NUMERO_WHATSAPP}?text=${encodeURIComponent(mensagem)}`;
    window.open(url, "_blank");
}

// ... (resto das funções salvarEdicao e excluirRegistro permanecem iguais)