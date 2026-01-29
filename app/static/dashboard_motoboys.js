{% extends "base.html" %}
{% block content %}

<h3 class="mb-4">Ranking de Motoboys</h3>

<table class="table table-striped align-middle">
    <thead class="table-dark">
        <tr>
            <th>#</th>
            <th>Motoboy</th>
            <th>Entregas</th>
            <th>KM Percorridos</th>
            <th>Total Pago (R$)</th>
        </tr>
    </thead>
    <tbody>
        {% for m, ent, km, valor in dados %}
        <tr>
            <td>{{ loop.index }}</td>
            <td>{{ m }}</td>
            <td>{{ ent }}</td>
            <td>{{ "%.2f"|format(km) }}</td>
            <td>R$ {{ "%.2f"|format(valor) }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>

{% endblock %}
