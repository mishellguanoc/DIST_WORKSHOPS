"""Measure bytes, latency and processing overhead for the three cases.

A:         POST /webhook with schemas validated on both sides.
A-control: POST /control/webhook, the same payloads without validation.
B:         POST /messages, the service with no schema.

Requests alternate between cases, so slow drift affects all of them equally.
"""

import argparse
import csv
import json
import platform
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

from clients import messages_client, webhook_client
from common.payloads import make_farewell_payload, make_webhook_payload

CASES = ["A", "A-control", "B"]
CLIENT_STAGES = ["validate_request", "serialize", "parse", "validate_response"]
SERVER_STAGES = ["parse", "validate_request", "handle", "validate_response", "serialize"]
FIELDS = (
    [
        "case",
        "index",
        "status",
        "expected",
        "request_head_bytes",
        "request_body_bytes",
        "response_head_bytes",
        "response_body_bytes",
        "timing_header_bytes",
        "rtt_ms",
        "server_total_ms",
        "transfer_ms",
    ]
    + [f"client_{stage}_ms" for stage in CLIENT_STAGES]
    + [f"server_{stage}_ms" for stage in SERVER_STAGES]
)


def is_expected(case, result):
    status = result["response"].status_code
    if case == "A":
        return status == 200 and not result["response_errors"]
    if case == "A-control":
        return status == 200
    # About 20% of the customers are outside the 24 h window on purpose.
    error = result["answer"].get("error", {})
    return status == 200 or (status == 400 and error.get("code") == 131047)


def to_row(case, index, result):
    response = result["response"]
    client_ms = result["client_ms"]
    server_ms = result["server_ms"]
    request_head, request_body = result["request_bytes"]
    response_head, response_body = result["response_bytes"]
    timing_value = response.headers.get("server-timing", "")

    row = {
        "case": case,
        "index": index,
        "status": response.status_code,
        "expected": int(is_expected(case, result)),
        "request_head_bytes": request_head,
        "request_body_bytes": request_body,
        "response_head_bytes": response_head,
        "response_body_bytes": response_body,
        # The header exists only to measure, so the analysis can leave it out.
        "timing_header_bytes": len("server-timing") + len(timing_value) + 4,
        "rtt_ms": client_ms["rtt"],
        "server_total_ms": server_ms["total"],
        "transfer_ms": client_ms["rtt"] - server_ms["total"],
    }
    for stage in CLIENT_STAGES:
        row[f"client_{stage}_ms"] = client_ms.get(stage, 0.0)
    for stage in SERVER_STAGES:
        row[f"server_{stage}_ms"] = server_ms.get(stage, 0.0)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, help="IP address of the WSL machine")
    parser.add_argument("--ingestion-port", type=int, default=8000)
    parser.add_argument("--wa-mock-port", type=int, default=8001)
    parser.add_argument("--requests", type=int, default=1000)
    parser.add_argument("--warmup", type=int, default=100)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--out", type=Path, default=Path("results"))
    args = parser.parse_args()

    ingestion = f"http://{args.host}:{args.ingestion_port}"
    wa_mock = f"http://{args.host}:{args.wa_mock_port}"
    rounds = args.warmup + args.requests
    rng = random.Random(args.seed)
    webhooks = [make_webhook_payload(rng, index) for index in range(rounds)]
    farewells = [make_farewell_payload(rng, index) for index in range(rounds)]
    rows = {case: [] for case in CASES}

    with (
        httpx.Client(timeout=5) as client_a,
        httpx.Client(timeout=5) as client_control,
        httpx.Client(timeout=5) as client_b,
    ):
        senders = {
            "A": lambda i: webhook_client.exchange(
                client_a, f"{ingestion}/webhook", webhooks[i]
            ),
            "A-control": lambda i: messages_client.exchange(
                client_control, f"{ingestion}/control/webhook", webhooks[i]
            ),
            "B": lambda i: messages_client.exchange(
                client_b, f"{wa_mock}/messages", farewells[i]
            ),
        }

        try:
            servers = {
                "ingestion": client_a.get(f"{ingestion}/info").json(),
                "wa_mock": client_b.get(f"{wa_mock}/info").json(),
            }
            print(f"{rounds} rounds, {len(CASES)} cases, {args.warmup} rounds of warm-up")
            for index in range(rounds):
                # Rotating the order keeps any case from always running first.
                shift = index % len(CASES)
                for case in CASES[shift:] + CASES[:shift]:
                    result = senders[case](index)
                    if index >= args.warmup:
                        rows[case].append(to_row(case, index, result))
        except (httpx.TransportError, json.JSONDecodeError) as error:
            print(f"benchmark stopped: {error}")
            print("are both services running, and is the WSL IP still the same?")
            return 2

    args.out.mkdir(parents=True, exist_ok=True)
    for case, case_rows in rows.items():
        with open(args.out / f"raw_{case}.csv", "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(case_rows)

    metadata = {
        "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "requests_per_case": args.requests,
        "warmup_rounds": args.warmup,
        "seed": args.seed,
        "server_ip": args.host,
        "client": {
            "system": platform.system(),
            "release": platform.release(),
            "python": platform.python_version(),
        },
        "servers": servers,
    }
    (args.out / "meta.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"saved {args.requests} samples per case in {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
