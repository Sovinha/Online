let resumoGlobal = [];
let lojaAtual = "";
let financeiroGlobal = {};
let ajustes = {};

const form = document.getElementById("formCalculo");
const btnCalcular = document.getElementById("btnCalcular");
const feedback = document.getElementById("formFeedback");
const previewStats = document.getElementById("previewStats");
const previewLojaNome = document.getElementById("previewLojaNome");
const previewMotoboys = document.getElementById("previewMotoboys");
const previewEntregas = document.getElementById("previewEntregas");
const previewTotalFinal = document.getElementById("previewTotalFinal");

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    limparFeedback();

    btnCalcular.disabled = true;
    btnCalcular.innerHTML = '<span class="spinner-border spinner-border-sm"></span><span>Gerando preview...</span>';

    try {
        const fd = new FormData(form);
        const response = await fetch("/calcular-preview", { method: "POST", body: fd });
        const data = await response.json();

        if (!response.ok || data.error) {
            mostrarFeedback(data.error || "Nao foi possivel gerar o preview.");
            return;
        }

        resumoGlobal = data.resumo;
        lojaAtual = data.loja;
        financeiroGlobal = data.financeiro;
        ajustes = {};

        montarModal();
    } catch (error) {
        mostrarFeedback("Erro de conexao com o servidor.");
    } finally {
        btnCalcular.disabled = false;
        btnCalcular.innerHTML = '<i class="bi bi-play-circle"></i><span>Gerar preview de pagamento</span>';
    }
});

function mostrarFeedback(message) {
    feedback.textContent = message;
    feedback.classList.remove("d-none");
}

function limparFeedback() {
    feedback.textContent = "";
    feedback.classList.add("d-none");
}

function formatCurrency(value) {
    return new Intl.NumberFormat("pt-BR", {
        style: "currency",
        currency: "BRL"
    }).format(Number(value || 0));
}

function renderStats() {
    const totalPago = resumoGlobal.reduce((sum, item) => sum + Number(item.total || 0), 0);
    const totalEntregas = resumoGlobal.reduce((sum, item) => sum + Number(item.entregas || 0), 0);
    const totalTaxas = Number(financeiroGlobal.taxas_clientes || 0);
    const faturamento = Number(financeiroGlobal.faturamento || 0);
    const diferenca = totalTaxas - totalPago;

    previewStats.innerHTML = `
        <div class="preview-stat-card">
            <span class="preview-stat-label">Faturamento dos pedidos</span>
            <strong>${formatCurrency(faturamento)}</strong>
        </div>
        <div class="preview-stat-card">
            <span class="preview-stat-label">Taxas pagas pelos clientes</span>
            <strong>${formatCurrency(totalTaxas)}</strong>
        </div>
        <div class="preview-stat-card">
            <span class="preview-stat-label">Total inicial aos motoboys</span>
            <strong>${formatCurrency(totalPago)}</strong>
        </div>
        <div class="preview-stat-card ${diferenca >= 0 ? "is-positive" : "is-negative"}">
            <span class="preview-stat-label">Saldo frete x pagamento</span>
            <strong>${formatCurrency(diferenca)}</strong>
        </div>
        <div class="preview-stat-card">
            <span class="preview-stat-label">Entregas lidas</span>
            <strong>${totalEntregas}</strong>
        </div>
        <div class="preview-stat-card">
            <span class="preview-stat-label">Motoboys envolvidos</span>
            <strong>${resumoGlobal.length}</strong>
        </div>
    `;
}

function montarModal() {
    const tbody = document.getElementById("listaAjustes");
    tbody.innerHTML = "";

    renderStats();

    resumoGlobal.forEach((item) => {
        const grupo = item.grupo || item.entregador;
        ajustes[grupo] = { valor: 0, motivo: "" };

        const row = document.createElement("tr");
        row.innerHTML = `
            <td>
                <div class="motoboy-cell">
                    <strong>${item.entregador}</strong>
                    <small>${item.pedidos ? `Pedidos: ${item.pedidos}` : "Sem lista de pedidos"}</small>
                </div>
            </td>
            <td>
                <div class="turno-badge">${item.turno}</div>
            </td>
            <td class="text-center fw-semibold">${item.entregas}</td>
            <td class="text-end fw-semibold">${formatCurrency(item.total)}</td>
            <td>
                <div class="input-group input-group-sm app-money-group">
                    <span class="input-group-text">R$</span>
                    <input
                        type="number"
                        step="0.01"
                        class="form-control app-input"
                        placeholder="0.00"
                        oninput="updateAjuste('${escapeKey(grupo)}', this.value, ${item.total})"
                    >
                </div>
            </td>
            <td>
                <input
                    type="text"
                    class="form-control form-control-sm app-input"
                    placeholder="Motivo do ajuste"
                    onchange="setMotivo('${escapeKey(grupo)}', this.value)"
                >
            </td>
            <td class="text-end fw-bold final-value" id="final-${safeId(grupo)}">${formatCurrency(item.total)}</td>
        `;
        tbody.appendChild(row);
    });

    atualizarResumoFinal();

    const lojaLabel = form.querySelector('select[name="loja"] option:checked');
    previewLojaNome.textContent = lojaLabel ? lojaLabel.textContent.trim() : lojaAtual;
    previewMotoboys.textContent = resumoGlobal.length;
    previewEntregas.textContent = resumoGlobal.reduce((sum, item) => sum + Number(item.entregas || 0), 0);

    const modal = new bootstrap.Modal(document.getElementById("modalAjustes"));
    modal.show();
}

function safeId(value) {
    return String(value).replace(/[^a-zA-Z0-9]/g, "");
}

function escapeKey(value) {
    return String(value).replace(/'/g, "\\'");
}

function updateAjuste(motoboy, valor, original) {
    const ajuste = parseFloat(valor || 0);
    ajustes[motoboy].valor = ajuste;
    const totalFinal = Number(original) + ajuste;
    document.getElementById(`final-${safeId(motoboy)}`).innerText = formatCurrency(totalFinal);
    atualizarResumoFinal();
}

function setMotivo(motoboy, valor) {
    ajustes[motoboy].motivo = valor;
}

function atualizarResumoFinal() {
    const totalFinal = resumoGlobal.reduce((sum, item) => {
        const chave = item.grupo || item.entregador;
        const ajuste = Number((ajustes[chave] || {}).valor || 0);
        return sum + Number(item.total || 0) + ajuste;
    }, 0);

    previewTotalFinal.textContent = formatCurrency(totalFinal);
}

document.getElementById("confirmarAjustes").onclick = async () => {
    const btn = document.getElementById("confirmarAjustes");
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span><span>Salvando...</span>';

    try {
        const response = await fetch("/calcular-confirmar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                loja: lojaAtual,
                resumo: resumoGlobal,
                financeiro: financeiroGlobal,
                ajustes: ajustes
            })
        });

        const result = await response.json();

        if (result.ok) {
            window.location.href = "/historico";
            return;
        }

        mostrarFeedback(result.error || "Nao foi possivel salvar o historico.");
    } catch (error) {
        mostrarFeedback("Erro de rede ao tentar salvar.");
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-check2-circle"></i><span>Confirmar e salvar</span>';
    }
};
