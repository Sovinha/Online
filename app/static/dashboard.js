// Variáveis globais para armazenar as instâncias
let chartLoja = null;
let chartEficiencia = null;

function renderizarGraficos() {
    // 1. Destruir gráficos existentes para evitar sobreposição
    if (chartLoja) chartLoja.destroy();
    if (chartEficiencia) chartEficiencia.destroy();

    // Estilo comum para fontes
    const fontStyle = { family: "'Helvetica Neue', 'Arial', sans-serif", size: 12 };

    // 2. Gráfico de Custos por Loja (Barras Modernas)
    const ctxLoja = document.getElementById("graficoLoja").getContext("2d");
    chartLoja = new Chart(ctxLoja, {
        type: "bar",
        data: {
            labels: dadosLoja.labels,
            datasets: [{
                label: "Total Gasto",
                data: dadosLoja.values,
                backgroundColor: "rgba(13, 110, 253, 0.8)",
                borderColor: "#0d6efd",
                borderWidth: 1,
                borderRadius: 8, // Barras arredondadas ficam mais modernas
                hoverBackgroundColor: "#0a58ca"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }, // Esconde legenda óbvia
                tooltip: {
                    padding: 12,
                    callbacks: {
                        label: (ctx) => ` R$ ${ctx.parsed.y.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { drawBorder: false, color: "#f0f0f0" },
                    ticks: { ...fontStyle, callback: (v) => 'R$ ' + v }
                },
                x: { grid: { display: false }, ticks: fontStyle }
            }
        }
    });

    // 3. Gráfico de Saúde Financeira (Rosca/Doughnut)
    // Calculamos o quanto das taxas cobre o pagamento e quanto é "custo extra"
    const prejuizo = Math.max(0, dadosFin.pago - dadosFin.recebido);
    const coberto = dadosFin.recebido;

    const ctxEficiencia = document.getElementById("graficoEficiencia").getContext("2d");
    chartEficiencia = new Chart(ctxEficiencia, {
        type: "doughnut",
        data: {
            labels: ["Coberto por Taxas", "Custo Empresa (Extra)"],
            datasets: [{
                data: [coberto, prejuizo],
                backgroundColor: ["#198754", "#dc3545"],
                hoverOffset: 15,
                borderWidth: 0,
                weight: 0.5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%', // Cria o efeito de rosca fina elegante
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { pointStyle: 'circle', usePointStyle: true, padding: 20, font: fontStyle }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const val = context.raw;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const perc = ((val / total) * 100).toFixed(1);
                            return ` R$ ${val.toLocaleString('pt-BR', {minimumFractionDigits: 2})} (${perc}%)`;
                        }
                    }
                }
            }
        }
    });
}

document.addEventListener("DOMContentLoaded", renderizarGraficos);