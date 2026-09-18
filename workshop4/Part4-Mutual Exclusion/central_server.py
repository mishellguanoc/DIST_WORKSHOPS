"""
Mutual Exclusion - Central Resource Server approach - Part 4 of Workshop 4 - Distributed Systems

Single-process simulation of N processes competing for one shared resource
through a central coordinator (the server). A process that wants the
resource sends a REQUEST; the server grants it immediately if the resource
is free, otherwise it queues the request (FIFO) and grants it later when
the current holder releases. There is no real networking: everything runs
as a single simulated timeline so the ordering is deterministic to read.

Rules:
    - Only one process may hold the resource at a time (mutual exclusion).
    - Requests are granted in the order they arrive (FIFO queue), so no
      process waits forever (no starvation).
    - A process must RELEASE before anyone else can be granted access.

Usage:
    python central_server.py [n] [rounds]
    (missing arguments are asked interactively)

Example:
    python central_server.py 4 15
"""

import sys
import random
import time

STEP_DELAY = 0.3  # seconds between printed rounds, so it reads like a live trace


def read_int(prompt, arg_value, default):
    if arg_value is not None:
        return int(arg_value)
    raw = input(prompt).strip()
    return int(raw) if raw else default


class CentralServer:
    """Owns the shared resource. Processes never talk to each other, only to this."""

    def __init__(self):
        self.holder = None
        self.queue = []

    def request(self, pid):
        if self.holder is None:
            self.holder = pid
            print(f"  [SERVER] GRANT  -> P{pid} (recurso estaba libre)")
            return True
        self.queue.append(pid)
        print(f"  [SERVER] QUEUE  -> P{pid} (ocupado por P{self.holder}), cola={self.queue}")
        return False

    def release(self, pid):
        print(f"  [SERVER] RELEASE<- P{pid}")
        self.holder = None
        if self.queue:
            next_pid = self.queue.pop(0)
            self.holder = next_pid
            print(f"  [SERVER] GRANT  -> P{next_pid} (siguiente en cola), cola={self.queue}")
            return next_pid
        return None


def main():
    n = read_int("Numero de procesos (default 4): ", sys.argv[1] if len(sys.argv) > 1 else None, 4)
    rounds = read_int("Numero de rondas a simular (default 15): ", sys.argv[2] if len(sys.argv) > 2 else None, 15)

    server = CentralServer()
    state = ["idle"] * n       # idle | waiting | holding
    hold_left = [0] * n
    stats = {"requests": 0, "grants": 0}

    print("=== Simulacion de Exclusion Mutua - Servidor Central ===")
    print(f"Procesos: {n}  Rondas: {rounds}")
    print("Un proceso IDLE puede pedir el recurso; el servidor lo otorga si esta libre")
    print("o lo encola (FIFO) si esta ocupado. Solo un proceso a la vez puede tenerlo.\n")

    for round_num in range(1, rounds + 1):
        print(f"--- Ronda {round_num} ---")
        for pid in range(n):
            if state[pid] == "idle":
                if random.random() < 0.4:
                    stats["requests"] += 1
                    print(f"  [P{pid}] REQUEST recurso")
                    if server.request(pid):
                        state[pid] = "holding"
                        hold_left[pid] = random.randint(1, 3)
                        stats["grants"] += 1
                    else:
                        state[pid] = "waiting"
                else:
                    print(f"  [P{pid}] idle")
            elif state[pid] == "waiting":
                print(f"  [P{pid}] esperando en cola...")
            elif state[pid] == "holding":
                print(f"  [P{pid}] usando el recurso ({hold_left[pid]} rondas restantes)")
                hold_left[pid] -= 1
                if hold_left[pid] == 0:
                    next_holder = server.release(pid)
                    state[pid] = "idle"
                    if next_holder is not None:
                        state[next_holder] = "holding"
                        hold_left[next_holder] = random.randint(1, 3)
                        stats["grants"] += 1
        time.sleep(STEP_DELAY)
        print()

    print("=== Resumen ===")
    print(f"  Requests totales: {stats['requests']}   Grants totales: {stats['grants']}")
    print("  Exclusion mutua garantizada: el servidor solo tiene un 'holder' a la vez,")
    print("  y solo lo reasigna despues de un RELEASE explicito.")


if __name__ == "__main__":
    main()
