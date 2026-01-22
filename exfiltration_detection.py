import argparse
import json
import math
import random
from dataclasses import dataclass
from datetime import datetime
from statistics import median
from typing import Dict, Iterable, List, Tuple


@dataclass
class Record:
    user: str
    bytes_out: int
    bytes_in: int
    destinations: int
    hour: int


def build_dataset() -> List[Record]:
    random.seed(7)
    records: List[Record] = []
    for i in range(120):
        records.append(
            Record(
                user=f"user_{i % 12}",
                bytes_out=random.randint(10_000, 80_000),
                bytes_in=random.randint(20_000, 120_000),
                destinations=random.randint(1, 6),
                hour=random.randint(8, 18),
            )
        )
    records.append(Record(user="user_3", bytes_out=980_000, bytes_in=40_000, destinations=24, hour=2))
    records.append(Record(user="user_7", bytes_out=1_200_000, bytes_in=60_000, destinations=30, hour=1))
    return records


def parse_hour(value: object) -> int:
    if isinstance(value, int):
        return max(0, min(23, value))
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
            return parsed.hour
        except Exception:
            return 12
    return 12


def parse_record(item: Dict[str, object], index: int) -> Record:
    return Record(
        user=str(item.get("user", f"user_{index}")),
        bytes_out=int(item.get("bytes_out", 0)),
        bytes_in=int(item.get("bytes_in", 0)),
        destinations=int(item.get("destinations", 1)),
        hour=parse_hour(item.get("hour") or item.get("timestamp")),
    )


def load_records(input_path: str | None) -> List[Record]:
    if input_path is None:
        return build_dataset()
    with open(input_path, "r", encoding="utf-8") as handle:
        raw = handle.read().strip()
    if not raw:
        return []
    if raw.startswith("["):
        data = json.loads(raw)
    else:
        data = [json.loads(line) for line in raw.splitlines() if line.strip()]
    return [parse_record(item, idx) for idx, item in enumerate(data)]


def robust_z(value: float, med: float, mad: float) -> float:
    if mad == 0:
        return 0.0
    return 0.6745 * (value - med) / mad


def build_baseline(records: Iterable[Record]) -> Dict[str, Dict[str, Tuple[float, float]]]:
    features: Dict[str, Dict[str, List[float]]] = {}
    for record in records:
        ratios = record.bytes_out / (record.bytes_in + 1)
        hour_dev = abs(record.hour - 13)
        bucket = features.setdefault(record.user, {"bytes_out": [], "destinations": [], "ratio": [], "hour_dev": []})
        bucket["bytes_out"].append(record.bytes_out)
        bucket["destinations"].append(record.destinations)
        bucket["ratio"].append(ratios)
        bucket["hour_dev"].append(hour_dev)

    baselines: Dict[str, Dict[str, Tuple[float, float]]] = {}
    for user, values in features.items():
        baselines[user] = {}
        for key, items in values.items():
            med = median(items)
            deviations = [abs(v - med) for v in items]
            mad = median(deviations) if deviations else 0.0
            baselines[user][key] = (med, mad)
    return baselines


def score_with_baseline(record: Record, baseline: Dict[str, Tuple[float, float]]) -> Tuple[float, List[str]]:
    ratio = record.bytes_out / (record.bytes_in + 1)
    hour_dev = abs(record.hour - 13)
    values = {
        "bytes_out": float(record.bytes_out),
        "destinations": float(record.destinations),
        "ratio": ratio,
        "hour_dev": float(hour_dev),
    }
    score = 0.0
    reasons = []
    for key, value in values.items():
        med, mad = baseline.get(key, (value, 0.0))
        z = robust_z(value, med, mad)
        if z > 0:
            score += z
        if z >= 3:
            reasons.append(key)
    return score, reasons


def rule_flags(record: Record) -> List[str]:
    flags = []
    if record.bytes_out >= 500_000:
        flags.append("bytes_out_spike")
    if record.destinations >= 15:
        flags.append("new_destinations")
    if record.hour <= 5:
        flags.append("off_hours")
    if record.bytes_out > record.bytes_in * 8:
        flags.append("upload_ratio")
    return flags


def try_isolation_forest(features: List[List[float]]) -> Tuple[bool, List[float]]:
    try:
        from sklearn.ensemble import IsolationForest  # type: ignore
    except Exception:
        return False, []
    model = IsolationForest(contamination=0.05, random_state=7)
    model.fit(features)
    raw_scores = model.decision_function(features)
    scores = [-s for s in raw_scores]
    return True, scores


def score_records(records: List[Record], use_ml: bool) -> Tuple[List[float], List[List[str]]]:
    baselines = build_baseline(records)
    reasons_list: List[List[str]] = []
    for record in records:
        score, reasons = score_with_baseline(record, baselines.get(record.user, {}))
        reasons_list.append(reasons + rule_flags(record))

    features = [[r.bytes_out, r.bytes_in, r.destinations, r.hour] for r in records]
    if use_ml and len(records) >= 20:
        ok, scores = try_isolation_forest(features)
        if ok:
            return scores, reasons_list
    return [score_with_baseline(r, baselines.get(r.user, {}))[0] for r in records], reasons_list


def risk_level(score: float) -> str:
    if score >= 6:
        return "high"
    if score >= 4:
        return "medium"
    if score >= 3:
        return "low"
    return "info"


def summarize(alerts: List[Dict[str, object]]) -> Dict[str, object]:
    risk_counts: Dict[str, int] = {}
    reason_counts: Dict[str, int] = {}
    for alert in alerts:
        risk = str(alert.get("risk", "unknown"))
        risk_counts[risk] = risk_counts.get(risk, 0) + 1
        for reason in alert.get("reasons", []):
            reason_counts[str(reason)] = reason_counts.get(str(reason), 0) + 1
    top_reasons = sorted(reason_counts.items(), key=lambda item: item[1], reverse=True)[:5]
    return {"alerts": len(alerts), "risk_counts": risk_counts, "top_reasons": top_reasons}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Exfiltration detection with robust scoring")
    parser.add_argument("--input", help="Path to JSON or JSONL input")
    parser.add_argument("--output", help="Path to JSON output")
    parser.add_argument("--stats", help="Path to JSON stats output")
    parser.add_argument("--top", type=int, default=10, help="Top N alerts to output")
    parser.add_argument("--threshold", type=float, default=3.0, help="Minimum score for alert")
    parser.add_argument("--no-ml", action="store_true", help="Disable Isolation Forest")
    parser.add_argument("--explain", action="store_true", help="Add explanations to alerts")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_records(args.input)
    scores, reasons_list = score_records(records, use_ml=not args.no_ml)
    alerts = []
    for record, score, reasons in zip(records, scores, reasons_list):
        if score < args.threshold:
            continue
        alert = {
            "user": record.user,
            "bytes_out": record.bytes_out,
            "bytes_in": record.bytes_in,
            "destinations": record.destinations,
            "hour": record.hour,
            "score": round(score, 2),
            "risk": risk_level(score),
            "reasons": sorted(set(reasons)),
        }
        if args.explain:
            alert["explain"] = {
                "ratio": round(record.bytes_out / (record.bytes_in + 1), 2),
                "off_hours": record.hour <= 5,
            }
        alerts.append(alert)
    alerts = sorted(alerts, key=lambda item: item["score"], reverse=True)[: args.top]

    output = json.dumps(alerts, ensure_ascii=True, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(output)
    else:
        print(output)
    if args.stats:
        summary = summarize(alerts)
        with open(args.stats, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(summary, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
