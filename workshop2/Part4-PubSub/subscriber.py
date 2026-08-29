"""
Publisher-Subscriber - Multiple publishers / multiple subscribers
Part 4 of Workshop 2 - Distributed Systems

A single subscriber process can connect to SEVERAL publishers at the same
time and subscribe to one or more topics (services). It uses a poller so
it can receive messages from any of the connected sockets as they arrive.

Usage:
    python subscriber.py <topic1,topic2,...> <host1:port1,host2:port2,...>

Example (subscribe to WEATHER and STOCKS, published on two different
publishers):
    python subscriber.py WEATHER,STOCKS localhost:15001,localhost:15002
"""

import zmq
import sys


def main():
    if len(sys.argv) >= 2:
        topics = [t.strip().upper() for t in sys.argv[1].split(",")]
    else:
        topics_str = input("Topics to subscribe to (comma separated, e.g. WEATHER,STOCKS): ")
        topics = [t.strip().upper() for t in topics_str.split(",") if t.strip()]

    if len(sys.argv) >= 3:
        targets = [t.strip() for t in sys.argv[2].split(",")]
    else:
        targets_str = input("Publisher addresses to connect to (comma separated, e.g. localhost:15001,localhost:15002): ")
        targets = [t.strip() for t in targets_str.split(",") if t.strip()]

    context = zmq.Context()
    s = context.socket(zmq.SUB)

    for target in targets:
        addr = f"tcp://{target}"
        s.connect(addr)
        print(f"Connected to publisher at {addr}")

    for topic in topics:
        s.setsockopt_string(zmq.SUBSCRIBE, topic)
        print(f"Subscribed to topic '{topic}'")

    poller = zmq.Poller()
    poller.register(s, zmq.POLLIN)

    print("Waiting for messages... (Ctrl+C to stop)\n")
    try:
        while True:
            events = dict(poller.poll())
            if s in events:
                msg = s.recv_string()
                print("Received:", msg)
    except KeyboardInterrupt:
        print("\nSubscriber stopped.")


if __name__ == "__main__":
    main()
