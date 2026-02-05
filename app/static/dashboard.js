// Variáveis globais para armazenar as instâncias dos gráficos
let chartLoja = null;
let chartEficiencia = null;

function renderizarGraficos() {
    // 1. Destruir gráficos existentes para evitar bugs ao filtrar
    if (chartLoja) chartLoja.destroy();
    if (chartEficiencia) chartEficiencia.destroy();

    // 2. Gráfico de Custos por Loja (Barras)
    const ctxLoja = document.getElementById("graficoLoja").getContext("2d");
    chartLoja = new Chart(ctxLoja, {
        type: "bar",
        data: {
            labels: dadosLoja.labels,
            datasets: [{
                label: "Total Gasto (R$)",
                data: dadosLoja.values,
                backgroundColor: "#0d6efd"
            }]
        },
        options: {
            responsive: true,
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return "R$ " + context.parsed.y.toLocaleString('pt-BR', { minimumFractionDigits: 2 });
                        }
                    }
                }
            }
        }
    });

    // 3. Gráfico de Eficiência (Comparativo)
    const ctxEficiencia = document.getElementById("graficoEficiencia").getContext("2d");
    chartEficiencia = new Chart(ctxEficiencia, {
        type: "bar",
        data: {
            labels: ["Comparativo de Fretes"],
            datasets: [
                {
                    label: "Taxas Recebidas (Clientes)",
                    data: [dadosFin.recebido],
                    backgroundColor: "#198754"
                },
                {
                    label: "Taxas Pagas (Motoboys)",
                    data: [dadosFin.pago],
                    backgroundColor: "#dc3545"
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return 'R$ ' + value.toLocaleString('pt-BR');
                        }
                    }
                }
            }
        }
    });
}

// Inicializa os gráficos assim que a página carregar
document.addEventListener("DOMContentLoaded", renderizarGraficos);