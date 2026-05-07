const compareForm = document.getElementById("formConferenciaPedidos");
const compareFeedback = document.getElementById("compareFeedback");
const compareResult = document.getElementById("compareResult");
const compareTableBody = document.getElementById("compareTableBody");
const compareCount = document.getElementById("compareCount");
const btnCompararPedidos = document.getElementById("btnCompararPedidos");

function showCompareError(message) {
    compareFeedback.textContent = message;
    compareFeedback.classList.remove("d-none");
}

function clearCompareError() {
    compareFeedback.textContent = "";
    compareFeedback.classList.add("d-none");
}

function renderDifferences(items) {
    if (!items || !items.length) {
        compareCount.textContent = "Sem divergencias";
        compareTableBody.innerHTML = `
            <tr>
                <td colspan="2" class="text-center text-muted py-4">Nenhum pedido divergente encontrado.</td>
            </tr>
        `;
        return;
    }

    compareCount.textContent = `${items.length} divergencias`;
    compareTableBody.innerHTML = items.map(item => `
        <tr>
            <td class="fw-semibold">${item.pedido}</td>
            <td>${formatDifferenceText(item)}</td>
        </tr>
    `).join("");
}

function formatDifferenceText(item) {
    if (item.tipo === "Motoboy divergente") {
        return `Encontra-se com ${item.motoboy_cardapio} -> ${item.motoboy}`;
    }

    if (item.tipo === "Faltando no Cardapio Web") {
        return `Encontra-se com ${item.motoboy} no Food e nao entrou no Cardapio Web`;
    }

    if (item.tipo === "Faltando no Food") {
        return `Encontra-se com ${item.motoboy} no Cardapio Web e nao apareceu no Food`;
    }

    return item.motoboy || "-";
}

compareForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearCompareError();
    compareResult.classList.add("d-none");

    btnCompararPedidos.disabled = true;
    btnCompararPedidos.innerHTML = '<span class="spinner-border spinner-border-sm"></span><span>Comparando...</span>';

    try {
        const response = await fetch("/conferencia-pedidos/analisar", {
            method: "POST",
            body: new FormData(compareForm),
        });

        const data = await response.json();

        if (!response.ok || data.error) {
            showCompareError(data.error || "Nao foi possivel comparar os relatorios.");
            return;
        }

        renderDifferences(data.differences);
        compareResult.classList.remove("d-none");
    } catch (error) {
        showCompareError("Erro de conexao ao comparar os relatorios.");
    } finally {
        btnCompararPedidos.disabled = false;
        btnCompararPedidos.innerHTML = '<i class="bi bi-search"></i><span>Comparar</span>';
    }
});
