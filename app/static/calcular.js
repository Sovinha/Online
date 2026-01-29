let resumoGlobal = [];
let lojaAtual = "";
let ajustes = {};

document.getElementById("formCalculo").addEventListener("submit", async e => {
    e.preventDefault();

    const fd = new FormData(e.target);
    const r = await fetch("/calcular-preview", { method: "POST", body: fd });
    const d = await r.json();

    resumoGlobal = d.resumo;
    lojaAtual = d.loja;
    ajustes = {};

    montarModal();
});

function montarModal() {
    const tbody = document.getElementById("listaAjustes");
    tbody.innerHTML = "";

    resumoGlobal.forEach(r => {
        ajustes[r.entregador] = { valor: 0, motivo: "" };

        tbody.innerHTML += `
        <tr>
            <td>${r.entregador}</td>
            <td>R$ ${r.total.toFixed(2)}</td>
            <td>
                <input type="number" step="0.01"
                       class="form-control"
                       onchange="setValor('${r.entregador}', this.value)">
            </td>
            <td>
                <input type="text"
                       class="form-control"
                       placeholder="Motivo do ajuste"
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
    const r = await fetch("/calcular-confirmar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            loja: lojaAtual,
            resumo: resumoGlobal,
            ajustes: ajustes
        })
    });

    if (r.ok) {
        window.location.href = "/historico";
    } else {
        alert("Erro ao confirmar cálculo");
    }
};
