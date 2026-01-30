{% extends "base.html" %}
{% block content %}

<div class="d-flex justify-content-between align-items-center mb-4">
    <h3 class="mb-0">🏆 Ranking de Motoboys</h3>
    <div class="d-print-none">
        <button onclick="window.print()" class="btn btn-outline-secondary">
            🖨️ Imprimir
        </button>
    </div>
</div>

<div class="card mb-4 shadow-sm d-print-none">
    <div class="card-body bg-light">
        <form method="GET" action="/dashboard-motoboys" class="row g-2">
            <div class="col-md-2">
                <label class="small fw-bold">Unidade</label>
                <select name="loja" class="form-select">
                    <option value="">Todas</option>
                    <option value="express" {% if loja == 'express' %}selected{% endif %}>Express</option>
                    <option value="bessa" {% if loja == 'bessa' %}selected{% endif %}>Bessa</option>
                </select>
            </div>
            <div class="col-md-2">
                <label class="small fw-bold">Turno</label>
                <select name="turno" class="form-select">
                    <option value="">Todos</option>
                    <option value="Almoço" {% if turno == 'Almoço' %}selected{% endif %}>Almoço</option>
                    <option value="Jantar" {% if turno == 'Jantar' %}selected{% endif %}>Jantar</option>
                </select>
            </div>
            <div class="col-md-3">
                <label class="small fw-bold">Data Início</label>
                <input type="date" name="data_inicio" class="form-control" value="{{ data_inicio }}">
            </div>
            <div class="col-md-3">
                <label class="small fw-bold">Data Fim</label>
                <input type="date" name="data_fim" class="form-control" value="{{ data_fim }}">
            </div>
            <div class="col-md-2 d-flex align-items-end">
                <button type="submit" class="btn btn-primary w-100">🔍 Filtrar</button>
            </div>
        </form>
    </div>
</div>

<div class="card shadow-sm">
    <div class="table-responsive">
        <table class="table table-hover align-middle mb-0">
            <thead class="table-dark">
                <tr>
                    <th class="text-center">#</th>
                    <th>Motoboy</th>
                    <th class="text-center">Entregas</th>
                    <th class="text-center">KM Totais</th>
                    <th class="text-center">KM Médio/Entrega</th>
                    <th class="text-end">Total Pago (R$)</th>
                </tr>
            </thead>
            <tbody>
                {% for m, ent, km_total, valor in dados %}
                <tr>
                    <td class="text-center">
                        {% if loop.index == 1 %} 🥇 
                        {% elif loop.index == 2 %} 🥈 
                        {% elif loop.index == 3 %} 🥉 
                        {% else %} {{ loop.index }} 
                        {% endif %}
                    </td>
                    <td class="fw-bold">{{ m }}</td>
                    <td class="text-center">{{ ent }}</td>
                    <td class="text-center">{{ "%.2f"|format(km_total) }} km</td>
                    <td class="text-center text-muted">
                        {# Cálculo do KM médio em tempo real #}
                        {{ "%.2f"|format(km_total / ent) if ent > 0 else 0 }} km
                    </td>
                    <td class="text-end fw-bold text-success">
                        R$ {{ "%.2f"|format(valor) }}
                    </td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="6" class="text-center py-4 text-muted">
                        Nenhum dado encontrado para o período ou filtros selecionados.
                    </td>
                </tr>
                {% endfor %}
            </tbody>
            {% if dados %}
            <tfoot class="table-light fw-bold">
                <tr>
                    <td colspan="2" class="text-end">TOTAIS DO FILTRO:</td>
                    <td class="text-center">{{ dados|sum(attribute='1') }}</td>
                    <td class="text-center">{{ "%.2f"|format(dados|sum(attribute='2')) }} km</td>
                    <td></td>
                    <td class="text-end text-primary">R$ {{ "%.2f"|format(dados|sum(attribute='3')) }}</td>
                </tr>
            </tfoot>
            {% endif %}
        </table>
    </div>
</div>

<style>
    @media print {
        .d-print-none { display: none !important; }
        .card { border: none !important; }
    }
</style>

{% endblock %}