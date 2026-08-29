"""
Pipeline communication: Source -> Broker -> Worker
Part 6 of Workshop 2 - Distributed Systems

A source generates work items and PUSHes them to the broker's frontend
socket. Several source processes can run at the same time, each
identified by a source id, and all of them feed the same broker.

Usage:
    python source.py <source_id> [broker_host] [broker_port] [num_jobs]

Example:
    python source.py S1 localhost 13001 10
"""

import zmq
import time
import pickle
import random
import sys


def main():
    source_id = sys.argv[1] if len(sys.argv) >= 2 else input("Source id (e.g. S1): ") or "S1"
    broker_host = sys.argv[2] if len(sys.argv) >= 3 else (input("Broker host [localhost]: ") or "localhost")
    broker_port = int(sys.argv[3]) if len(sys.argv) >= 4 else int(input("Broker frontend port [13001]: ") or 13001)
    num_jobs = int(sys.argv[4]) if len(sys.argv) >= 5 else int(input("Number of jobs to send [10]: ") or 10)

    context = zmq.Context()
    s = context.socket(zmq.PUSH)
    s.connect(f"tcp://{broker_host}:{broker_port}")

    for i in range(num_jobs):
        workload = random.randint(1, 10)  # simulated "cost" of the job, in tenths of a second
        work = (source_id, i, workload)

        print(f"[{source_id}] Sending:", work)
        s.send(pickle.dumps(work))

        time.sleep(0.2)

    print(f"[{source_id}] Done sending {num_jobs} jobs.")


if __name__ == "__main__":
    main()
