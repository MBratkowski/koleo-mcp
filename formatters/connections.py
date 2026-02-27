from koleo.api.types import V3ConnectionResult


def format_connection(conn: V3ConnectionResult, price: dict | None = None) -> str:
    dep = (conn.get("departure") or "")[:16]
    arr = (conn.get("arrival") or "")[:16]
    duration = conn.get("duration", 0)
    changes = conn.get("changes", 0)
    legs = conn.get("legs", [])
    train_names = [leg.get("train_full_name", "") for leg in legs if leg.get("leg_type") == "train_leg"]
    price_str = f"  [{price['price']}]" if price else ""
    change_str = f"{changes} change(s)" if changes else "direct"
    return f"{dep} -> {arr}  {duration}min  {change_str}  via {', '.join(train_names)}{price_str}"


def summarize_connections(
    connections: list[V3ConnectionResult],
    start_name: str,
    end_name: str,
    prices: dict[str, dict],
) -> str:
    lines = [f"Connections {start_name} -> {end_name}:"]
    for c in connections:
        lines.append("  " + format_connection(c, prices.get(c.get("uuid", ""))))
    if not connections:
        lines.append("  No connections found.")
    return "\n".join(lines)
