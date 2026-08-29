"""
Publisher-Subscriber - Multiple publishers / multiple subscribers
Part 4 of Workshop 2 - Distributed Systems

Each publisher instance offers ONE service (identified by a topic name,
e.g. "WEATHER", "STOCKS", "NEWS") and periodically broadcasts messages
prefixed with that topic. A subscriber can connect to several publishers
at once and subscribe to more than one topic (see subscriber.py).

Usage:
    python publisher.py <service_name> [host] [port]

Example:
    python publisher.py WEATHER 0.0.0.0 15001
    python publisher.py STOCKS  0.0.0.0 15002
"""

import zmq
import time
import sys
import random


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
        value = random.randint(0, 100)
        msg = f"{service} {time.asctime()} - #{cont} value={value}"
        print(f"[{service}] Sending: {msg}")
        s.send_string(msg)


if __name__ == "__main__":
    main()
