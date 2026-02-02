let historicoAtual = 0;
let modoVisualizacao = true;
let dadosCompletosCachorro = null;

const NUMERO_WHATSAPP = "558396300542";

// 1. ABRIR MODAL (DETALHES)
async function abrirModal(id, visualizar) {
    historicoAtual = id;
    modoVisualizacao = visualizar;

    const r = await fetch(`/historico/detalhes/${id}`);
    const d = await r.json();
    dadosCompletosCachorro = d; 

    const tbody = document.getElementById("modalBody");
    tbody.innerHTML = "";

    d.dados.forEach(i => {
        // Criamos a linha principal SEM a coluna de pedidos (ela fica escondida)
        tbody.innerHTML += `
        <tr>
            <td class="fw-bold text-primary text-start">${i.motoboy}</td>
            <td>
                ${i.entregas}
                <button class="btn btn-outline-primary btn-sm p-0 px-1 ms-2 border-0" type="button" 
                        onclick="toggleEntregas(${i.id})" title="Ver IDs detalhados">
                    🔍
                </button>
            </td>
            <td>${i.km_medio} km</td>
            <td>
                <input type="number" step="0.01" class="form-control form-control-sm text-center mx-auto" 
                       style="max-width: 100px;"
                       value="${i.valor_final}" 
                       ${modoVisualizacao ? "disabled" : ""} 
                       data-id="${i.id}">
            </td>
            <td>
                <input type="text" class="form-control form-control-sm" 
                       value="${i.motivo ?? ""}" 
                       ${modoVisualizacao ? "disabled" : ""} 
                       data-motivo="${i.id}">
            </td>
        </tr>
        <tr id="detalhe-entrega-${i.id}" style="display: none;" class="bg-light">
            <td colspan="5"> 
                <div class="mx-3 my-2 p-3 border-start border-primary border-4 shadow-sm bg-white rounded text-start">
                    <small class="text-muted d-block mb-1"><strong>IDs dos Pedidos vinculados:</strong></small>
                    <div class="col-pedidos">
                        ${i.pedidos || 'Nenhum ID registrado'}
                    </div>
                </div>
            </td>
        </tr>`;
    });

    // Ajusta visibilidade dos botões
    document.getElementById("btnSalvar").style.display = modoVisualizacao ? "none" : "inline-block";
    document.getElementById("btnWhatsapp").style.display = modoVisualizacao ? "inline-block" : "none";

    new bootstrap.Modal(document.getElementById("modalHistorico")).show();
}

// FUNÇÃO PARA MOSTRAR/ESCONDER ENTREGAS
function toggleEntregas(id) {
    const el = document.getElementById(`detalhe-entrega-${id}`);
    el.style.display = el.style.display === "none" ? "table-row" : "none";
}

// 2. ENVIAR WHATSAPP
function enviarWhatsapp() {
    if (!dadosCompletosCachorro) return;

    const d = dadosCompletosCachorro;
    
    let mensagem = `*RELATÓRIO DE ENTREGAS - ${d.loja.toUpperCase()}*\n`;
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

    document.querySelectorAll("[data-id]").forEach(i => {
        const id = i.dataset.id;
        const valor = parseFloat(i.value).toLocaleString('pt-BR', {minimumFractionDigits: 2});
        const motivo = document.querySelector(`[data-motivo="${id}"]`).value;

        const linhaPrincipal = i.closest("tr");
        const motoboy = linhaPrincipal.children[0].innerText;
        // Limpa o texto das entregas removendo a lupa
        const entregas = linhaPrincipal.children[1].innerText.replace('🔍', '').trim();
        
        // Busca os pedidos na linha de detalhe correspondente
        const detalheLinha = document.getElementById(`detalhe-entrega-${id}`);
        const pedidos = detalheLinha.querySelector('.col-pedidos').innerText.trim();

        mensagem += `• *${motoboy}:* R$ ${valor} (${entregas} entr.)\n`;
        mensagem += `  _Pedidos: ${pedidos}_${motivo ? `\n  _Motivo: ${motivo}_` : ""}\n\n`;
    });

    const url = `https://wa.me/${NUMERO_WHATSAPP}?text=${encodeURIComponent(mensagem)}`;
    window.open(url, "_blank");
}

// 3. SALVAR EDIÇÃO
async function salvarEdicao() {
    const editados = [];
    document.querySelectorAll("[data-id]").forEach(i => {
        const id = i.dataset.id;
        const valor = parseFloat(i.value);
        const motivo = document.querySelector(`[data-motivo="${id}"]`).value;
        editados.push({ id, valor, motivo });
    });

    try {
        const response = await fetch("/historico/editar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ dados: editados })
        });

        if (response.ok) {
            alert("✅ Alterações salvas com sucesso!");
            location.reload();
        } else {
            alert("❌ Erro ao salvar alterações.");
        }
    } catch (e) {
        alert("Erro de conexão ao salvar.");
    }
}

// 4. EXCLUIR REGISTRO
async function excluirRegistro(id) {
    if (!confirm("⚠️ Tem certeza que deseja excluir permanentemente este registro?")) return;

    try {
        const response = await fetch(`/historico/excluir/${id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (response.ok) {
            alert("🗑️ Registro removido com sucesso!");
            location.reload();
        } else {
            const err = await response.json();
            alert("Erro ao excluir: " + (err.error || "Erro no servidor"));
        }
    } catch (error) {
        alert("Erro de conexão ao tentar excluir.");
    }
}