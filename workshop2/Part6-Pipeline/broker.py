"""
Pipeline communication: Source -> Broker -> Worker
Part 6 of Workshop 2 - Distributed Systems

The broker sits between (possibly many) sources and (possibly many)
workers. It exposes a single input socket (PULL) where every source
pushes its work, and a single output socket (PUSH) from which every
worker pulls work. zmq.proxy() takes care of the forwarding, and PUSH/PULL
sockets automatically load-balance across all connected peers (round
robin), so work is spread evenly among whichever workers are connected.

Usage:
    python broker.py [frontend_port] [backend_port]

Defaults: frontend (sources -> broker) = 13001
          backend  (broker -> workers) = 13002
"""

import zmq
import sys


def main():
    frontend_port = int(sys.argv[1]) if len(sys.argv) >= 2 else 13001
    backend_port = int(sys.argv[2]) if len(sys.argv) >= 3 else 13002

    context = zmq.Context()

    # Single input: sources connect here and PUSH work
    frontend = context.socket(zmq.PULL)
    frontend.bind(f"tcp://*:{frontend_port}")

    # Single output: workers connect here and PULL work
    backend = context.socket(zmq.PUSH)
    backend.bind(f"tcp://*:{backend_port}")

    print(f"Broker running.")
    print(f"  Sources connect (PUSH) to tcp://<broker-ip>:{frontend_port}")
    print(f"  Workers connect (PULL) to tcp://<broker-ip>:{backend_port}")
    print("Forwarding messages... (Ctrl+C to stop)")

    try:
        zmq.proxy(frontend, backend)
    except KeyboardInterrupt:
        print("\nBroker stopped.")
    finally:
        frontend.close()
        backend.close()
        context.term()


if __name__ == "__main__":
    main()
