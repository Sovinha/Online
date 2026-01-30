let resumoGlobal = [];
let lojaAtual = "";
let financeiroGlobal = {}; // NOVO: Variável para segurar os valores do patrão
let ajustes = {};

document.getElementById("formCalculo").addEventListener("submit", async e => {
    e.preventDefault();

    const fd = new FormData(e.target);
    const r = await fetch("/calcular-preview", { method: "POST", body: fd });
    const d = await r.json();

    if (d.error) {
        alert(d.error);
        return;
    }

    resumoGlobal = d.resumo;
    lojaAtual = d.loja;
    financeiroGlobal = d.financeiro; // NOVO: Armazena faturamento e taxas_clientes
    ajustes = {};

    console.log("Dados financeiros recebidos:", financeiroGlobal); // Para conferência no F12
    montarModal();
});

function montarModal() {
    const tbody = document.getElementById("listaAjustes");
    tbody.innerHTML = "";

    resumoGlobal.forEach(r => {
        // Inicializa o objeto de ajuste para cada motoboy
        ajustes[r.entregador] = { valor: 0, motivo: "" };

        tbody.innerHTML += `
        <tr>
            <td>${r.entregador} <br><small class="text-muted">${r.entregas} ent. | ${r.turno}</small></td>
            <td>R$ ${r.total.toFixed(2)}</td>
            <td>
                <input type="number" step="0.01"
                       class="form-control"
                       placeholder="0.00"
                       onchange="setValor('${r.entregador}', this.value)">
            </td>
            <td>
                <input type="text"
                       class="form-control"
                       placeholder="Ex: Bônus chuva"
                       onchange="setMotivo('${r.entregador}', this.value)">
            </td>
        </tr>`;
    });

    new bootstrap.Modal(document.getElementById("modalAjustes")).show();
}

function setValor(m, v) {
    ajustes[m].valor = parseFloat(v || 0);
}

function setMotivo(m, v) {
    ajustes[m].motivo = v;
}

document.getElementById("confirmarAjustes").onclick = async () => {
    // Desabilitar botão para evitar cliques duplos
    const btn = document.getElementById("confirmarAjustes");
    btn.disabled = true;
    btn.innerText = "Salvando...";

    const r = await fetch("/calcular-confirmar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            loja: lojaAtual,
            resumo: resumoGlobal,
            financeiro: financeiroGlobal, // NOVO: Agora o faturamento vai para o banco!
            ajustes: ajustes
        })
    });

    const resultado = await r.json();

    if (resultado.ok) {
        window.location.href = "/historico";
    } else {
        alert("Erro ao confirmar cálculo: " + (resultado.message || "Erro desconhecido"));
        btn.disabled = false;
        btn.innerText = "Confirmar e Salvar";
    }
};