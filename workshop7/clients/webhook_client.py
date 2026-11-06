"""Activity 1: wa_mock webhook dispatcher, validating both ways (machine A, Windows)."""

import argparse
import json
import platform
import random
import sys

import httpx

from common.payloads import make_webhook_payload
from common.timing import (
    StageTimer,
    describe_cost,
    parse_server_timing,
    request_wire_bytes,
    response_wire_bytes,
)
from common.validation import validate_request, validate_response

# Not the hostname: WSL inherits it from Windows, so both machines share it.
MACHINE = platform.system()


def log(text):
    print(f"[wa_mock@{MACHINE}] {text}", flush=True)


def exchange(client, url, message):
    """Validate, send and check one message; return what happened and its cost.

    When the message breaks the schema nothing is sent and "response" is None.
    """
    timer = StageTimer()
    request_errors = validate_request(message)
    timer.lap("validate_request")
    if request_errors:
        return {"request_errors": request_errors, "response": None}

    body = json.dumps(message, separators=(",", ":")).encode("utf-8")
    request = client.build_request(
        "POST", url, content=body, headers={"Content-Type": "application/json"}
    )
    timer.lap("serialize")

    response = client.send(request)
    timer.lap("rtt")

    try:
        answer = json.loads(response.content)
    except ValueError:
        answer = None
    timer.lap("parse")

    if answer is None:
        response_errors = [{"path": "$", "message": "response is not valid JSON"}]
    else:
        response_errors = validate_response(answer)
    timer.lap("validate_response")

    return {
        "request_errors": [],
        "response": response,
        "answer": answer,
        "response_errors": response_errors,
        "client_ms": timer.stages_ms,
        "server_ms": parse_server_timing(response.headers.get("server-timing", "")),
        "request_bytes": request_wire_bytes(request),
        "response_bytes": response_wire_bytes(response),
    }


def report(url, message, result):
    log(f"request schema: {'INVALID' if result['request_errors'] else 'valid'}")
    if result["response"] is None:
        for error in result["request_errors"]:
            log(f"  {error['path']}: {error['message']}")
        log("not sent")
        return False

    response = result["response"]
    response_errors = result["response_errors"]
    log(f"sent to {url}: {json.dumps(message)}")
    log(f"response {response.status_code}: {response.text}")
    log(f"response schema: {'INVALID' if response_errors else 'valid'}")
    for error in response_errors:
        log(f"  {error['path']}: {error['message']}")

    for line in describe_cost(result):
        log(line)
    return response.is_success and not response_errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, help="IP address of the WSL machine")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}/webhook"
    rng = random.Random(args.seed)
    all_ok = True

    with httpx.Client(timeout=5) as client:
        for index in range(1, args.count + 1):
            message = make_webhook_payload(rng, index)
            try:
                result = exchange(client, url, message)
            except httpx.TransportError as error:
                log(f"cannot reach {url}: {error}")
                log("is the service running, and is the WSL IP still the same?")
                return 2
            all_ok = report(url, message, result) and all_ok

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
