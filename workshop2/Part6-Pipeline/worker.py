"""
Pipeline communication: Source -> Broker -> Worker
Part 6 of Workshop 2 - Distributed Systems

A worker connects (PULL) to the broker's backend socket and processes
whatever work item it receives. Several worker processes can run at the
same time, each identified by a worker id; the broker (via PUSH/PULL
round robin) spreads jobs coming from all sources across all connected
workers.

Usage:
    python worker.py <worker_id> [broker_host] [broker_port]

Example:
    python worker.py W1 localhost 13002
"""

import zmq
import time
import pickle
import sys


def main():
    worker_id = sys.argv[1] if len(sys.argv) >= 2 else input("Worker id (e.g. W1): ") or "W1"
    broker_host = sys.argv[2] if len(sys.argv) >= 3 else (input("Broker host [localhost]: ") or "localhost")
    broker_port = int(sys.argv[3]) if len(sys.argv) >= 4 else int(input("Broker backend port [13002]: ") or 13002)

    context = zmq.Context()
    r = context.socket(zmq.PULL)
    r.connect(f"tcp://{broker_host}:{broker_port}")

    print(f"[{worker_id}] Ready, connected to broker at {broker_host}:{broker_port}")

    count = 0
    while True:
        source_id, job_id, workload = pickle.loads(r.recv())
        count += 1

        print(f"[{worker_id}] Received job #{job_id} from {source_id} (workload={workload}) -> processing...")
        time.sleep(workload * 0.1)
        print(f"[{worker_id}] Finished job #{job_id} from {source_id} (total processed: {count})")


if __name__ == "__main__":
    main()
