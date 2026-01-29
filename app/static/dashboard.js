new Chart(document.getElementById("graficoLoja"), {
    type: "bar",
    data: {
        labels: dadosLoja.labels,
        datasets: [{
            label: "Total por Loja",
            data: dadosLoja.values
        }]
    }
});

new Chart(document.getElementById("graficoDia"), {
    type: "line",
    data: {
        labels: dadosDia.labels,
        datasets: [{
            label: "Total por Dia",
            data: dadosDia.values,
            tension: 0.3
        }]
    }
});
