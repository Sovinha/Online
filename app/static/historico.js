let historicoAtual = 0;
let dadosCompletosCachorro = null;
const NUMERO_WHATSAPP = "558396300542";

async function abrirModal(id, visualizar) {
    historicoAtual = id;
    try {
        const r = await fetch(`/historico/detalhes/${id}`);
        const d = await r.json();
        dadosCompletosCachorro = d;

        const tbody = document.getElementById("modalBody");
        if (tbody) {
            tbody.innerHTML = d.dados.map(i => `
                <tr>
                    <td class="text-start">${i.motoboy}</td>
                    <td>${i.entregas} <button class="btn btn-sm" onclick="toggleEntregas(${i.id})">🔍</button></td>
                    <td>${i.km_medio} km</td>
                    <td><input type="number" class="form-control form-control-sm mx-auto" style="width: 80px;" value="${i.valor_final}" ${visualizar ? "disabled" : ""} data-id="${i.id}"></td>
                    <td><input type="text" class="form-control form-control-sm" value="${i.motivo ?? ""}" ${visualizar ? "disabled" : ""} data-motivo="${i.id}"></td>
                </tr>
                <tr id="detalhe-entrega-${i.id}" style="display: none;"><td colspan="5" class="bg-light text-start small p-3">IDs: ${i.pedidos}</td></tr>
            `).join("");
        }

        const btnSalvar = document.getElementById("btnSalvar");
        const btnWhatsapp = document.getElementById("btnWhatsapp");

        if (btnSalvar) btnSalvar.style.display = visualizar ? "none" : "inline-block";
        if (btnWhatsapp) btnWhatsapp.style.display = visualizar ? "inline-block" : "none";

        const modalEl = document.getElementById("modalHistorico");
        if (modalEl) {
            const modalBusca = bootstrap.Modal.getOrCreateInstance(modalEl);
            modalBusca.show();
        }
    } catch (e) {
        console.error("Erro ao carregar detalhes:", e);
    }
}

function toggleEntregas(id) {
    const el = document.getElementById(`detalhe-entrega-${id}`);
    if (el) el.style.display = el.style.display === "none" ? "table-row" : "none";
}

function enviarWhatsapp() {
    const d = dadosCompletosCachorro;
    if (!d) return;

    const faturamento = Number(d.faturamento || 0);
    const taxasClientes = Number(d.taxas_clientes || 0);
    const pagoMotoboys = Number(d.pago_motoboys || 0);
    const cobertura = Number(d.cobertura || 0);
    const saldoFrete = taxasClientes - pagoMotoboys;

    let msg = `*RELATORIO DE FECHAMENTO - ${String(d.loja || "").toUpperCase()}*\n`;
    msg += `Data: ${d.data || "-"}\n`;
    msg += `Turno: ${d.turno || "-"}\n\n`;
    msg += `*RESUMO FINANCEIRO*\n`;
    msg += `Faturamento dos pedidos: R$ ${faturamento.toFixed(2)}\n`;
    msg += `Taxas pagas pelos clientes: R$ ${taxasClientes.toFixed(2)}\n`;
    msg += `Total pago aos motoboys: R$ ${pagoMotoboys.toFixed(2)}\n`;
    msg += `Cobertura do frete: ${cobertura.toFixed(2)}%\n`;
    msg += `${saldoFrete >= 0 ? "Saldo do frete" : "Complemento da empresa"}: R$ ${Math.abs(saldoFrete).toFixed(2)}\n\n`;

    if (d.erros && d.erros !== "None" && d.erros.trim() !== "") {
        msg += `*OCORRENCIAS*\n${d.erros}\n\n`;
    }

    msg += `*PAGAMENTO POR MOTOBOY*\n`;
    let posicao = 1;
    document.querySelectorAll("[data-id]").forEach(input => {
        const row = input.closest("tr");
        const motoboy = row.children[0].innerText;
        const entregasTexto = row.children[1].innerText.replace("🔍", "").trim();
        const quantidadePedidos = parseInt(entregasTexto, 10) || 0;
        msg += `${posicao}. ${motoboy}: ${quantidadePedidos} pedidos | R$ ${Number(input.value || 0).toFixed(2)}\n`;
        posicao += 1;
    });

    msg += `\n*TOTAL DO FECHAMENTO*: R$ ${pagoMotoboys.toFixed(2)}`;

    window.open(`https://wa.me/${NUMERO_WHATSAPP}?text=${encodeURIComponent(msg)}`, "_blank");
}

function abrirModalErro(id, textoAtual) {
    const textoLimpo = (textoAtual === "None" || !textoAtual) ? "" : textoAtual;

    const inputId = document.getElementById("erro_registro_id");
    const inputTexto = document.getElementById("erro_texto");

    if (inputId) inputId.value = id;
    if (inputTexto) inputTexto.value = textoLimpo;

    const modalErroEl = document.getElementById("modalErro");
    if (modalErroEl) {
        const modalErro = bootstrap.Modal.getOrCreateInstance(modalErroEl);
        modalErro.show();
    }
}

async function salvarErro() {
    const idInput = document.getElementById("erro_registro_id");
    const textoInput = document.getElementById("erro_texto");

    if (!idInput || !textoInput) return;

    const id = idInput.value;
    const texto = textoInput.value;
    const btn = document.querySelector("#modalErro .btn-salvar-filipeia") ||
        document.querySelector('#modalErro button[onclick="salvarErro()"]');

    const originalText = btn ? btn.innerHTML : "Salvar";

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Aguarde...';
    }

    try {
        const r = await fetch(`/historico/salvar-erro/${id}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ erro: texto })
        });

        if (r.ok) {
            location.reload();
        } else {
            alert("Erro ao salvar no servidor.");
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        }
    } catch (error) {
        alert("Erro de conexao.");
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }
}

function visualizarErro(texto) {
    if (!texto || texto === "None" || texto.trim() === "") {
        alert("Filipéia Trattoria:\nNenhuma ocorrencia registrada para este turno.");
    } else {
        alert("OCORRENCIAS REGISTRADAS:\n\n" + texto);
    }
}

async function excluirRegistro(id) {
    if (confirm("Deseja realmente excluir permanentemente este registro?")) {
        try {
            const r = await fetch(`/historico/excluir/${id}`, { method: "POST" });
            if (r.ok) location.reload();
        } catch (e) {
            alert("Erro ao excluir.");
        }
    }
}
