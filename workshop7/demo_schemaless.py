"""Bad data against the service without a schema (Activity 2)."""

import argparse
import random
import sys

import httpx

from common.payloads import SIMULATED_NOW, customer_last_seen, make_farewell_payload


def open_window_customer():
    limit = SIMULATED_NOW.timestamp() - 24 * 3600
    seen = customer_last_seen()
    return next(c for c, last in seen.items() if last.timestamp() >= limit)


def bad_messages(valid):
    return [
        ("missing field", {k: v for k, v in valid.items() if k != "body"}),
        ("wrong type", {**valid, "body": 12345}),
        ("extra field", {**valid, "priority": "high"}),
        ("invalid value", {**valid, "kind": "farewel"}),
    ]


def show(tag, label, response):
    print(f"  [{tag}] {label}: HTTP {response.status_code} {response.text}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, help="IP address of the WSL machine")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}/messages"
    valid = make_farewell_payload(random.Random(7), 1)
    valid["customer_id"] = open_window_customer()
    no_customer = {k: v for k, v in valid.items() if k != "customer_id"}
    expected = 0

    try:
        with httpx.Client(timeout=5) as client:
            print("Control: a valid farewell")
            response = client.post(url, json=valid)
            expected += response.status_code == 200
            show("OK" if response.status_code == 200 else "UNEXPECTED", "valid", response)

            print("Bad data: nothing stops it")
            for label, message in bad_messages(valid):
                response = client.post(url, json=message)
                accepted = response.status_code == 200
                expected += accepted
                show("ACCEPTED" if accepted else "UNEXPECTED", label, response)

            print("Missing customer_id: reported as an expired 24 h window")
            response = client.post(url, json=no_customer)
            misleading = (
                response.status_code == 400
                and response.json().get("error", {}).get("code") == 131047
            )
            expected += misleading
            show("WRONG ERROR" if misleading else "UNEXPECTED", "no customer", response)
    except httpx.TransportError as error:
        print(f"cannot reach {url}: {error}")
        print("is the service running, and is the WSL IP still the same?")
        return 2

    print(f"{expected}/6 results as expected")
    return 0 if expected == 6 else 1


if __name__ == "__main__":
    sys.exit(main())
