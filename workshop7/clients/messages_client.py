"""Activity 2: scheduler farewell dispatcher, with no schema (machine A, Windows)."""

import argparse
import json
import platform
import random
import sys

import httpx

from common.payloads import make_farewell_payload
from common.timing import (
    StageTimer,
    describe_cost,
    parse_server_timing,
    request_wire_bytes,
    response_wire_bytes,
)

MACHINE = platform.system()


def log(text):
    print(f"[scheduler@{MACHINE}] {text}", flush=True)


def exchange(client, url, message):
    """Send one message and return what happened and its cost, without validating."""
    timer = StageTimer()

    body = json.dumps(message, separators=(",", ":")).encode("utf-8")
    request = client.build_request(
        "POST", url, content=body, headers={"Content-Type": "application/json"}
    )
    timer.lap("serialize")

    response = client.send(request)
    timer.lap("rtt")

    answer = json.loads(response.content)
    timer.lap("parse")

    return {
        "response": response,
        "answer": answer,
        "client_ms": timer.stages_ms,
        "server_ms": parse_server_timing(response.headers.get("server-timing", "")),
        "request_bytes": request_wire_bytes(request),
        "response_bytes": response_wire_bytes(response),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, help="IP address of the WSL machine")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}/messages"
    rng = random.Random(args.seed)

    with httpx.Client(timeout=5) as client:
        for index in range(1, args.count + 1):
            message = make_farewell_payload(rng, index)
            try:
                result = exchange(client, url, message)
            except httpx.TransportError as error:
                log(f"cannot reach {url}: {error}")
                log("is the service running, and is the WSL IP still the same?")
                return 2
            log(f"sent to {url}: {json.dumps(message)}")
            log(f"response {result['response'].status_code}: {result['response'].text}")
            for line in describe_cost(result):
                log(line)

    return 0


if __name__ == "__main__":
    sys.exit(main())
