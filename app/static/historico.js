// Variáveis de controle
let historicoAtual = 0;
let dadosCompletosCachorro = null;
const NUMERO_WHATSAPP = "558396300542";

/**
 * --- GESTÃO DE DETALHES E WHATSAPP ---
 */

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
            `).join('');
        }

        // Ajusta visibilidade dos botões no modal principal
        const btnSalvar = document.getElementById("btnSalvar");
        const btnWhatsapp = document.getElementById("btnWhatsapp");
        
        if (btnSalvar) btnSalvar.style.display = visualizar ? "none" : "inline-block";
        if (btnWhatsapp) btnWhatsapp.style.display = visualizar ? "inline-block" : "none";
        
        // Abre o modal de detalhes (padrão do site)
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
    if(!d) return;

    let msg = `*RELATÓRIO - ${d.loja.toUpperCase()}*\nFaturamento: R$ ${d.faturamento}\nCobertura: ${d.cobertura}%\n\n`;
    
    // Inclui os erros no relatório do WhatsApp se existirem
    if (d.erros && d.erros !== "None" && d.erros.trim() !== "") {
        msg += `*OCORRÊNCIAS:* ${d.erros}\n\n`;
    }

    document.querySelectorAll("[data-id]").forEach(i => {
        const row = i.closest("tr");
        const motoboy = row.children[0].innerText;
        msg += `• *${motoboy}*: R$ ${i.value}\n`;
    });

    window.open(`https://wa.me/${NUMERO_WHATSAPP}?text=${encodeURIComponent(msg)}`, "_blank");
}

/**
 * --- GESTÃO DE ERROS E OBSERVAÇÕES ---
 */

function abrirModalErro(id, textoAtual) {
    // Limpa o texto se for nulo ou "None" vindo do Python
    const textoLimpo = (textoAtual === 'None' || !textoAtual) ? "" : textoAtual;
    
    const inputId = document.getElementById('erro_registro_id');
    const inputTexto = document.getElementById('erro_texto');
    
    if (inputId) inputId.value = id;
    if (inputTexto) inputTexto.value = textoLimpo;
    
    const modalErroEl = document.getElementById('modalErro');
    if (modalErroEl) {
        const modalErro = bootstrap.Modal.getOrCreateInstance(modalErroEl);
        modalErro.show();
    }
}

async function salvarErro() {
    const idInput = document.getElementById('erro_registro_id');
    const textoInput = document.getElementById('erro_texto');
    
    if (!idInput || !textoInput) return;

    const id = idInput.value;
    const texto = textoInput.value;
    
    // Seleciona o botão de salvar (seja pela classe ou pelo onclick)
    const btn = document.querySelector('#modalErro .btn-salvar-filipeia') || 
                document.querySelector('#modalErro button[onclick="salvarErro()"]');
    
    const originalText = btn ? btn.innerHTML : "Salvar";

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Aguarde...';
    }

    try {
        const r = await fetch(`/historico/salvar-erro/${id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ erro: texto })
        });

        if (r.ok) {
            location.reload(); // Recarrega para mostrar o ícone de que tem erro
        } else {
            alert("Erro ao salvar no servidor.");
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        }
    } catch (error) {
        alert("Erro de conexão.");
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }
}

function visualizarErro(texto) {
    // Função para mostrar o erro sem precisar abrir o modal de edição
    if (!texto || texto === "None" || texto.trim() === "") {
        alert("📊 Filipéia Trattoria:\nNenhuma ocorrência registrada para este turno.");
    } else {
        alert("⚠️ OCORRÊNCIAS REGISTRADAS:\n\n" + texto);
    }
}

async function excluirRegistro(id) {
    if (confirm("Deseja realmente excluir permanentemente este registro?")) {
        try {
            const r = await fetch(`/historico/excluir/${id}`, { method: 'POST' });
            if (r.ok) location.reload();
        } catch (e) {
            alert("Erro ao excluir.");
        }
    }
}