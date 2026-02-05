let resumoGlobal = [];
let lojaAtual = "";
let financeiroGlobal = {}; 
let ajustes = {};

document.getElementById("formCalculo").addEventListener("submit", async e => {
    e.preventDefault();

    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Processando...';

    try {
        const fd = new FormData(e.target);
        const r = await fetch("/calcular-preview", { method: "POST", body: fd });
        const d = await r.json();

        if (d.error) {
            alert("Erro: " + d.error);
            return;
        }

        resumoGlobal = d.resumo;
        lojaAtual = d.loja;
        financeiroGlobal = d.financeiro; 
        ajustes = {};

        montarModal();
    } catch (err) {
        alert("Erro na conexão com o servidor.");
    } finally {
        btn.disabled = false;
        btn.innerText = "Calcular";
    }
});

function montarModal() {
    const tbody = document.getElementById("listaAjustes");
    tbody.innerHTML = "";

    resumoGlobal.forEach(r => {
        ajustes[r.entregador] = { valor: 0, motivo: "" };

        tbody.innerHTML += `
        <tr>
            <td>
                <strong>${r.entregador}</strong><br>
                <small class="text-muted">${r.entregas} ent. | ${r.turno}</small>
            </td>
            <td class="fw-bold">R$ ${r.total.toFixed(2)}</td>
            <td>
                <div class="input-group input-group-sm">
                    <span class="input-group-text">R$</span>
                    <input type="number" step="0.01" class="form-control" 
                           placeholder="0.00" oninput="updateAjuste('${r.entregador}', this.value, ${r.total}, this)">
                </div>
            </td>
            <td>
                <input type="text" class="form-control form-control-sm" 
                       placeholder="Motivo (ex: bônus)" onchange="setMotivo('${r.entregador}', this.value)">
            </td>
            <td class="text-end fw-bold text-primary" id="final-${r.entregador.replace(/\s+/g, '')}">
                R$ ${r.total.toFixed(2)}
            </td>
        </tr>`;
    });

    const modal = new bootstrap.Modal(document.getElementById("modalAjustes"));
    modal.show();
}

// Atualiza o valor do ajuste e o mostrador de Total Final em tempo real
function updateAjuste(motoboy, valor, original, inputElement) {
    const v = parseFloat(valor || 0);
    ajustes[motoboy].valor = v;
    
    // Atualiza a célula de "Total Final" na tabela para o patrão ver a soma
    const totalFinal = original + v;
    const displayId = `final-${motoboy.replace(/\s+/g, '')}`;
    document.getElementById(displayId).innerText = `R$ ${totalFinal.toFixed(2)}`;
}

function setMotivo(m, v) {
    ajustes[m].motivo = v;
}

document.getElementById("confirmarAjustes").onclick = async () => {
    const btn = document.getElementById("confirmarAjustes");
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Gravando no Banco...';

    try {
        const r = await fetch("/calcular-confirmar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                loja: lojaAtual,
                resumo: resumoGlobal,
                financeiro: financeiroGlobal,
                ajustes: ajustes
            })
        });

        const resultado = await r.json();

        if (resultado.ok) {
            // Sucesso! Redireciona para o histórico
            window.location.href = "/historico";
        } else {
            alert("Erro ao salvar: " + (resultado.message || "Erro desconhecido"));
            btn.disabled = false;
            btn.innerText = "Confirmar e Salvar";
        }
    } catch (err) {
        alert("Erro de rede ao tentar salvar.");
        btn.disabled = false;
        btn.innerText = "Confirmar e Salvar";
    }
};