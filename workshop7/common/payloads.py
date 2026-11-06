"""Synthetic messages; the same seed always produces the same payloads."""

import random
from datetime import datetime, timedelta, timezone

START = datetime(2026, 11, 5, 8, 0, tzinfo=timezone.utc)
SIMULATED_NOW = START + timedelta(days=1)
CUSTOMERS = 500

BODIES = [
    "Hello, is my order ready?",
    "Thanks, that solved my problem.",
    "What time do you close today?",
    "I would like to change my delivery address, please.",
    "Could you send me the invoice for last month?",
    "The payment went through but I have not received a confirmation yet.",
]
EDGE_CASES = ["duplicate", "late_delivery", "out_of_order"]
FAREWELLS = [
    "Thanks for contacting us. We are closing this conversation for now.",
    "It looks like everything is sorted. Write to us again whenever you need.",
    "We have not heard from you, so we will close this chat. Have a nice day!",
]


def make_webhook_payload(rng, index):
    message = {
        "msg_id": f"m-{index:06d}",
        "customer_id": f"c-{rng.randrange(CUSTOMERS):04d}",
        "session_id": f"s-{rng.randrange(2000):05d}",
        "t_customer": (START + timedelta(seconds=rng.randrange(86400))).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "body": rng.choice(BODIES),
        "delivery_attempt": rng.choices([1, 2, 3], weights=[90, 8, 2])[0],
    }
    if rng.random() < 0.05:
        message["edge_case"] = rng.choice(EDGE_CASES)
    return message


def make_farewell_payload(rng, index):
    return {
        "customer_id": f"c-{rng.randrange(CUSTOMERS):04d}",
        "kind": "farewell",
        "in_reply_to": f"m-{index:06d}",
        "body": rng.choice(FAREWELLS),
        "fencing_meta": {
            "conv_version": rng.randint(1, 20),
            "lease_epoch": rng.randint(1, 5),
        },
    }


def customer_last_seen(seed=7):
    """Last message time per customer; about 20% fall outside the 24 h window."""
    rng = random.Random(seed)
    return {
        f"c-{index:04d}": SIMULATED_NOW - timedelta(hours=rng.uniform(0, 30))
        for index in range(CUSTOMERS)
    }
