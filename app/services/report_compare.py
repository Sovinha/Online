from collections import defaultdict
import re
import unicodedata

import pandas as pd


def _normalize(text):
    text = "" if text is None else str(text).strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"\s+", " ", text)


def _find_column(df, *candidates):
    normalized = {column: _normalize(column) for column in df.columns}
    wanted = {_normalize(candidate) for candidate in candidates}

    for column, column_normalized in normalized.items():
        if column_normalized in wanted:
            return column
    return None


def _display_name(name):
    normalized = _normalize(name)
    if not normalized or normalized == "nan":
        return "Sem entregador"

    aliases = {
        "jose ricardo": "Ricardo",
        "gilvan dos santos silva": "Gilvan",
        "anderson araujo pereira": "Anderson",
        "ithalo santos": "Ithalo",
        "alex pinho vital": "Alex",
    }

    if normalized in aliases:
        return aliases[normalized]

    if "ricardo" in normalized and "jose" in normalized:
        return "Ricardo"

    return str(name).strip().split()[0].title()


def _order_id(value):
    if pd.isna(value):
        return None
    try:
        return str(int(float(value)))
    except Exception:
        cleaned = re.sub(r"[^0-9]", "", str(value))
        return cleaned or None


def _extract_orders(df, source):
    if source == "cardapio":
        order_col = _find_column(df, "Número do pedido", "Numero do pedido")
        courier_col = _find_column(df, "Entregador", "Motoboy")
        status_col = _find_column(df, "Status")
        valid_statuses = {"concluido", "finalizado", "entregue"}
    elif source == "food":
        order_col = _find_column(df, "N Pedido", "Numero do pedido", "Número do pedido")
        courier_col = _find_column(df, "Entregador", "Motoboy")
        status_col = _find_column(df, "Situação", "Situacao", "Status")
        valid_statuses = {"concluido", "finalizado", "entregue"}
    else:
        raise ValueError("Fonte de relatorio desconhecida.")

    if not order_col:
        raise ValueError(f"Não foi possível identificar a coluna do número do pedido no relatório {source}.")

    orders = {}
    duplicates = defaultdict(list)
    without_courier = []

    for _, row in df.iterrows():
        status = _normalize(row.get(status_col)) if status_col else ""
        if status and status not in valid_statuses:
            continue

        order = _order_id(row.get(order_col))
        if not order:
            continue

        courier = _display_name(row.get(courier_col)) if courier_col else "Sem entregador"
        if courier == "Sem entregador":
            without_courier.append(order)

        if order in orders:
            duplicates[order].append(courier)
            continue

        orders[order] = {
            "pedido": order,
            "motoboy": courier,
        }

    return {
        "orders": orders,
        "duplicates": {pedido: nomes for pedido, nomes in duplicates.items()},
        "without_courier": sorted(set(without_courier), key=lambda x: int(x)),
    }


def compare_reports(cardapio_df, food_df):
    cardapio = _extract_orders(cardapio_df, "cardapio")
    food = _extract_orders(food_df, "food")

    missing_in_cardapio = defaultdict(list)
    missing_in_food = defaultdict(list)
    diverging_couriers = []
    differences = []

    for pedido, info in sorted(food["orders"].items(), key=lambda item: int(item[0])):
        if pedido not in cardapio["orders"]:
            missing_in_cardapio[info["motoboy"]].append(pedido)
            differences.append({
                "tipo": "Faltando no Cardapio Web",
                "pedido": pedido,
                "motoboy": info["motoboy"],
            })
        elif cardapio["orders"][pedido]["motoboy"] != info["motoboy"]:
            diverging_couriers.append({
                "pedido": pedido,
                "food_motoboy": info["motoboy"],
                "cardapio_motoboy": cardapio["orders"][pedido]["motoboy"],
            })
            differences.append({
                "tipo": "Motoboy divergente",
                "pedido": pedido,
                "motoboy": info["motoboy"],
                "motoboy_cardapio": cardapio["orders"][pedido]["motoboy"],
            })

    for pedido, info in sorted(cardapio["orders"].items(), key=lambda item: int(item[0])):
        if pedido not in food["orders"]:
            missing_in_food[info["motoboy"]].append(pedido)
            differences.append({
                "tipo": "Faltando no Food",
                "pedido": pedido,
                "motoboy": info["motoboy"],
            })

    return {
        "summary": {
            "cardapio_total": len(cardapio["orders"]),
            "food_total": len(food["orders"]),
            "missing_in_cardapio_total": sum(len(items) for items in missing_in_cardapio.values()),
            "missing_in_food_total": sum(len(items) for items in missing_in_food.values()),
            "diverging_couriers_total": len(diverging_couriers),
        },
        "missing_in_cardapio": [
            {"motoboy": motoboy, "pedidos": pedidos, "quantidade": len(pedidos)}
            for motoboy, pedidos in sorted(missing_in_cardapio.items())
        ],
        "missing_in_food": [
            {"motoboy": motoboy, "pedidos": pedidos, "quantidade": len(pedidos)}
            for motoboy, pedidos in sorted(missing_in_food.items())
        ],
        "diverging_couriers": diverging_couriers,
        "duplicates": {
            "cardapio": cardapio["duplicates"],
            "food": food["duplicates"],
        },
        "without_courier": {
            "cardapio": cardapio["without_courier"],
            "food": food["without_courier"],
        },
        "differences": differences,
    }
