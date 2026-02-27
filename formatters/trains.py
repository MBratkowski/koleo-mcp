from koleo.api.types import TrainDetail, TrainStop


def _format_time(t: dict | str | None) -> str:
    if not t:
        return "     "
    if isinstance(t, dict):
        return f"{t.get('hour', 0):02d}:{t.get('minute', 0):02d}"
    return str(t)[11:16]


def format_stop(stop: TrainStop) -> str:
    arr = _format_time(stop.get("arrival"))
    dep = _format_time(stop.get("departure"))
    name = stop.get("station_display_name") or stop.get("station_name", "?")
    platform = stop.get("platform", "")
    pos = f" pl.{platform}" if platform else ""
    dist_km = stop.get("distance", 0) / 1000
    return f"{dist_km:>6.1f}km  {arr} / {dep}  {name}{pos}"


def summarize_train_route(train: TrainDetail, stops: list[TrainStop]) -> str:
    lines = [
        f"{train.get('train_full_name', '?')}",
        f"  Runs: {train.get('run_desc', 'N/A')}",
        f"  {len(stops)} stops:",
    ]
    first_dist = stops[0]["distance"] if stops else 0
    for stop in stops:
        stop = dict(stop)
        stop["distance"] = stop["distance"] - first_dist
        lines.append("  " + format_stop(stop))
    return "\n".join(lines)
