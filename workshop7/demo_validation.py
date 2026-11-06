"""Negative cases for the service with predefined schemas (Activity 1).

The service must run with W7_FAULTS=1 for the invalid-response check.
"""

import argparse
import json
import random
import sys

import httpx

from clients.webhook_client import exchange
from common.payloads import make_webhook_payload
from common.validation import validate_response


def bad_messages(valid):
    return [
        ("missing field", {k: v for k, v in valid.items() if k != "body"}),
        ("wrong type", {**valid, "delivery_attempt": "1"}),
        ("extra field", {**valid, "priority": "high"}),
        ("invalid date", {**valid, "t_customer": "yesterday"}),
    ]


def first_error(errors):
    return f"{errors[0]['path']}: {errors[0]['message']}"[:80]


def show(passed, label, detail):
    print(f"  [{'OK' if passed else 'FAIL'}] {label}: {detail}")
    return passed


def check_valid_message(client, url, valid):
    result = exchange(client, url, valid)
    response = result["response"]
    passed = (
        response is not None
        and response.status_code == 200
        and not result["response_errors"]
    )
    detail = "accepted" if passed else "expected HTTP 200 and a valid response"
    return show(passed, "valid message", detail)


def check_client_blocks(client, url, label, message):
    result = exchange(client, url, message)
    if result["response"] is not None:
        return show(False, label, "was sent, but the client should block it")
    return show(True, label, f"not sent, {first_error(result['request_errors'])}")


def check_server_rejects(client, url, label, message):
    # Posting directly skips the client-side validation in exchange().
    response = client.post(url, json=message)
    answer = response.json()
    passed = (
        response.status_code == 422
        and answer.get("status") == "rejected"
        and not validate_response(answer)
    )
    if not passed:
        return show(False, label, f"expected HTTP 422, got {response.status_code}")
    return show(True, label, f"HTTP 422, {first_error(answer['errors'])}")


def check_invalid_response(client, url, valid):
    result = exchange(client, url, valid)
    response = result["response"]
    if response.status_code != 200:
        detail = f"got HTTP {response.status_code}; start the service with W7_FAULTS=1"
        return show(False, "fault route", detail)
    print(f"  received: {response.text}")
    passed = bool(result["response_errors"])
    detail = "client marked the response INVALID" if passed else "not detected"
    return show(passed, "invalid response", detail)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, help="IP address of the WSL machine")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"
    webhook_url = f"{base_url}/webhook"
    valid = make_webhook_payload(random.Random(7), 1)
    cases = bad_messages(valid)
    results = []

    try:
        with httpx.Client(timeout=5) as client:
            print("Control: a valid message goes through")
            results.append(check_valid_message(client, webhook_url, valid))

            print("Client validation: invalid messages are never sent")
            for label, message in cases:
                results.append(check_client_blocks(client, webhook_url, label, message))

            print("Server validation: client check skipped")
            for label, message in cases:
                results.append(
                    check_server_rejects(client, webhook_url, label, message)
                )

            print("Response validation: the server breaks the schema")
            results.append(
                check_invalid_response(client, f"{base_url}/faults/webhook", valid)
            )
    except (httpx.TransportError, json.JSONDecodeError) as error:
        print(f"cannot complete the demo against {base_url}: {error}")
        print("is the service running, and is the WSL IP still the same?")
        return 2

    print(f"{sum(results)}/{len(results)} checks passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
