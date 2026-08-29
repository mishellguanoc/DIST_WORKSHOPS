"""
Publisher-Subscriber - Multiple publishers / multiple subscribers
Part 4 of Workshop 2 - Distributed Systems

Each publisher instance offers ONE service (identified by a topic name,
e.g. "WEATHER", "STOCKS", "NEWS") and periodically broadcasts messages
prefixed with that topic. Each known service produces payload data that
matches what it represents (temperature/humidity for WEATHER, price for
STOCKS, a headline for NEWS); any other service name falls back to a
generic random value. A subscriber can connect to several publishers at
once and subscribe to more than one topic (see subscriber.py).

Usage:
    python publisher.py <service_name> [host] [port]

Example:
    python publisher.py WEATHER 0.0.0.0 15001
    python publisher.py STOCKS  0.0.0.0 15002
    python publisher.py NEWS    0.0.0.0 15003
"""

import zmq
import time
import sys
import random


NEWS_HEADLINES = [
    "Local team wins championship",
    "New tech breakthrough announced",
    "Markets react to policy change",
    "City council approves new budget",
    "Scientists discover new species",
]


def build_payload(service):
    """
    Builds message content appropriate for the given service/topic.
    Falls back to a generic random value for unknown services.
    """
    if service == "WEATHER":
        temperature = round(random.uniform(-5, 40), 1)
        humidity = random.randint(20, 100)
        return f"temperature={temperature}C humidity={humidity}%"
    elif service == "STOCKS":
        price = round(random.uniform(10, 500), 2)
        change = round(random.uniform(-5, 5), 2)
        return f"price={price} change={change:+.2f}"
    elif service == "NEWS":
        headline = random.choice(NEWS_HEADLINES)
        return f'headline="{headline}"'
    else:
        return f"value={random.randint(0, 100)}"


def main():
    if len(sys.argv) < 2:
        service = input("Enter the service/topic name this publisher offers (e.g. WEATHER): ").strip().upper()
    else:
        service = sys.argv[1].strip().upper()

    if len(sys.argv) >= 3:
        bindHost = sys.argv[2]
    else:
        bindHost = input("Enter bind host/IP [0.0.0.0]: ").strip() or "0.0.0.0"

    if len(sys.argv) >= 4:
        serverPort = int(sys.argv[3])
    else:
        try:
            serverPort = int(input("Enter port number [15000]: ") or 15000)
        except ValueError:
            serverPort = 15000

    context = zmq.Context()
    s = context.socket(zmq.PUB)

    p = f"tcp://{bindHost}:{serverPort}"
    s.bind(p)

    print(f"[{service}] Publisher listening on {p}")

    cont = 0
    while True:
        time.sleep(2)
        cont += 1
        payload = build_payload(service)
        msg = f"{service} {time.asctime()} - #{cont} {payload}"
        print(f"[{service}] Sending: {msg}")
        s.send_string(msg)


if __name__ == "__main__":
    main()
