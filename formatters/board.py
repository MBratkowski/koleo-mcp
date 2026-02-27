from koleo.api.types import TrainOnStationInfo


def format_train_on_station(train: TrainOnStationInfo, type: str = "departure") -> str:
    time_key = "departure" if type == "departure" else "arrival"
    time_val = train.get(time_key, "")
    time_str = time_val[:16] if time_val else "??:??"
    name = train.get("train_full_name", "")
    first_station = train["stations"][0]["name"] if train.get("stations") else ""
    platform = train.get("platform", "")
    track = train.get("track", "")
    pos = ""
    if platform:
        pos += f" pl.{platform}"
    if track:
        pos += f"/{track}"
    return f"{time_str}  {name}  ({first_station}){pos}"


def summarize_board(trains: list[TrainOnStationInfo], station_name: str, date_str: str, type: str) -> str:
    label = "Departures" if type == "departure" else "Arrivals"
    lines = [f"{station_name} -- {label} on {date_str}:"]
    lines += [format_train_on_station(t, type) for t in trains[:20]]
    if len(trains) > 20:
        lines.append(f"  ... and {len(trains) - 20} more")
    if not trains:
        lines.append("  No trains found for this time.")
    return "\n".join(lines)
