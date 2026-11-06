"""Summarize the benchmark: summary.json, a text table and the report figure."""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from benchmark.run_benchmark import CASES

CASE_LABELS = {"A": "A (schema)", "A-control": "A-control", "B": "B (no schema)"}
SURFACE = "#ffffff"
TEXT = "#0b0b0b"
MUTED = "#52514e"
GRID = "#e4e3df"

# Median time per group; each group adds up the columns listed for it.
STAGE_GROUPS = [
    (
        "JSON encode/decode",
        "#2a78d6",
        [
            "client_serialize_ms",
            "client_parse_ms",
            "server_parse_ms",
            "server_serialize_ms",
        ],
    ),
    (
        "Validation, client",
        "#eb6834",
        ["client_validate_request_ms", "client_validate_response_ms"],
    ),
    (
        "Validation, server",
        "#1baf7a",
        ["server_validate_request_ms", "server_validate_response_ms"],
    ),
    ("Service logic", "#eda100", ["server_handle_ms"]),
]


def load_case(directory, case):
    with open(directory / f"raw_{case}.csv", newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    columns = {
        name: np.array([float(row[name]) for row in rows])
        for name in rows[0]
        if name != "case"
    }
    return columns


def stats(values):
    return {
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "p95": float(np.percentile(values, 95)),
        "p99": float(np.percentile(values, 99)),
    }


def summarize(columns):
    request_bytes = columns["request_head_bytes"] + columns["request_body_bytes"]
    response_bytes = (
        columns["response_head_bytes"]
        + columns["response_body_bytes"]
        - columns["timing_header_bytes"]
    )
    client_ms = sum(
        columns[name]
        for name in columns
        if name.startswith("client_") and name.endswith("_ms")
    )
    stage_names = [name for name in columns if name.startswith(("client_", "server_"))]
    stage_names = [name for name in stage_names if name != "server_total_ms"]
    return {
        "samples": len(columns["rtt_ms"]),
        "unexpected": int(np.sum(columns["expected"] == 0)),
        "status_counts": {
            str(int(status)): count
            for status, count in sorted(Counter(columns["status"]).items())
        },
        "bytes": {
            "request_body": stats(columns["request_body_bytes"]),
            "response_body": stats(columns["response_body_bytes"]),
            "request_total": stats(request_bytes),
            "response_total": stats(response_bytes),
            "exchange_total": stats(request_bytes + response_bytes),
            "timing_header_excluded": stats(columns["timing_header_bytes"]),
        },
        "latency_ms": {
            "rtt": stats(columns["rtt_ms"]),
            "one_way_estimate": stats(columns["rtt_ms"] / 2),
            "transfer": stats(columns["transfer_ms"]),
        },
        "overhead_ms": {
            "client": stats(client_ms),
            "server": stats(columns["server_total_ms"]),
            "total": stats(client_ms + columns["server_total_ms"]),
        },
        "stages_ms": {name: stats(columns[name]) for name in stage_names},
    }


def print_tables(summary):
    cases = summary["cases"]
    print(f"Client: {summary['meta']['client']['system']}   ", end="")
    server = summary["meta"]["servers"]["ingestion"]
    print(f"Server: {server['system']} at {summary['meta']['server_ip']}")

    print("\nData per exchange (bytes, mean, HTTP head + body)")
    print(f"{'case':<10}{'samples':>8}{'errors':>7}{'request':>9}{'response':>9}{'total':>7}")
    for name in CASES:
        case = cases[name]
        data = case["bytes"]
        print(
            f"{name:<10}{case['samples']:>8}{case['unexpected']:>7}"
            f"{data['request_total']['mean']:>9.1f}"
            f"{data['response_total']['mean']:>9.1f}"
            f"{data['exchange_total']['mean']:>7.1f}"
        )

    print("\nLatency (ms)")
    print(f"{'case':<10}{'RTT med':>9}{'p95':>8}{'p99':>8}{'transfer':>10}{'one-way':>9}")
    for name in CASES:
        latency = cases[name]["latency_ms"]
        rtt = latency["rtt"]
        print(
            f"{name:<10}{rtt['median']:>9.3f}{rtt['p95']:>8.3f}{rtt['p99']:>8.3f}"
            f"{latency['transfer']['median']:>10.3f}"
            f"{latency['one_way_estimate']['median']:>9.3f}"
        )

    print("\nProcessing overhead (ms, median)")
    print(f"{'case':<10}{'client':>9}{'server':>9}{'total':>9}")
    for name in CASES:
        overhead = cases[name]["overhead_ms"]
        print(
            f"{name:<10}{overhead['client']['median']:>9.3f}"
            f"{overhead['server']['median']:>9.3f}"
            f"{overhead['total']['median']:>9.3f}"
        )

    schema = summary["schema_cost_median_ms"]
    print(
        f"\nSchema cost (A minus A-control): overhead {schema['overhead']:+.3f} ms, "
        f"RTT {schema['rtt']:+.3f} ms"
    )


def draw_figure(all_columns, summary, path):
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 7,
            "text.color": TEXT,
            "axes.labelcolor": MUTED,
            "xtick.color": MUTED,
            "ytick.color": TEXT,
        }
    )
    figure, (rtt_axis, stage_axis) = plt.subplots(
        2, 1, figsize=(3.5, 3.1), layout="constrained", sharey=True
    )
    positions = np.arange(len(CASES))
    labels = [CASE_LABELS[case] for case in CASES]

    medians = [summary["cases"][case]["latency_ms"]["rtt"]["median"] for case in CASES]
    rtt_axis.barh(positions, medians, height=0.6, color=MUTED)
    for position, case, median in zip(positions, CASES, medians):
        p95 = summary["cases"][case]["latency_ms"]["rtt"]["p95"]
        rtt_axis.annotate(
            f"{median:.2f} ms (p95 {p95:.2f})",
            (median, position),
            xytext=(3, 0),
            textcoords="offset points",
            va="center",
        )
    rtt_axis.set_title("Median round-trip time", loc="left", fontsize=8, color=TEXT)
    rtt_axis.set_xlabel("ms")
    rtt_axis.set_xlim(0, max(medians) * 1.6)

    starts = np.zeros(len(CASES))
    for label, color, names in STAGE_GROUPS:
        widths = np.array(
            [sum(np.median(all_columns[case][name]) for name in names) for case in CASES]
        )
        stage_axis.barh(
            positions,
            widths,
            left=starts,
            height=0.6,
            color=color,
            edgecolor=SURFACE,
            linewidth=0.8,
            label=label,
        )
        starts += widths
    for position, total in zip(positions, starts):
        stage_axis.annotate(
            f"{total:.3f} ms",
            (total, position),
            xytext=(3, 0),
            textcoords="offset points",
            va="center",
        )
    stage_axis.set_title(
        "Median processing time by stage", loc="left", fontsize=8, color=TEXT
    )
    stage_axis.set_xlabel("ms (client + server)")
    stage_axis.set_xlim(0, max(starts) * 1.25)
    stage_axis.legend(
        loc="upper center",
        bbox_to_anchor=(0.45, -0.32),
        ncol=2,
        frameon=False,
        fontsize=7,
    )

    rtt_axis.invert_yaxis()  # The y axis is shared, so this flips both panels.
    for axis in (rtt_axis, stage_axis):
        axis.set_yticks(positions, labels)
        axis.tick_params(length=0)
        axis.grid(axis="x", color=GRID, linewidth=0.5)
        axis.set_axisbelow(True)
        for side in ("top", "right", "left"):
            axis.spines[side].set_visible(False)
        axis.spines["bottom"].set_color(GRID)

    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=300, facecolor=SURFACE)
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", type=Path, default=Path("results"))
    parser.add_argument(
        "--figure", type=Path, default=Path("results/08_latency_overhead.png")
    )
    args = parser.parse_args()

    all_columns = {case: load_case(args.dir, case) for case in CASES}
    cases = {case: summarize(columns) for case, columns in all_columns.items()}
    summary = {
        "meta": json.loads((args.dir / "meta.json").read_text(encoding="utf-8")),
        "cases": cases,
        "schema_cost_median_ms": {
            "overhead": cases["A"]["overhead_ms"]["total"]["median"]
            - cases["A-control"]["overhead_ms"]["total"]["median"],
            "rtt": cases["A"]["latency_ms"]["rtt"]["median"]
            - cases["A-control"]["latency_ms"]["rtt"]["median"],
        },
    }
    (args.dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print_tables(summary)
    draw_figure(all_columns, summary, args.figure)
    print(f"\nsaved {args.dir / 'summary.json'} and {args.figure}")

    unexpected = sum(case["unexpected"] for case in cases.values())
    return 1 if unexpected else 0


if __name__ == "__main__":
    sys.exit(main())
