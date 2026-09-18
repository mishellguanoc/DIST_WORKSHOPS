"""
Mutual Exclusion - Distributed Token Ring approach - Part 4 of Workshop 4 - Distributed Systems

Single-process simulation of N processes arranged in a logical ring. A
single token circulates P0 -> P1 -> ... -> P(n-1) -> P0 -> ... Only the
process currently holding the token may enter its critical section (use
the shared resource); everyone else must wait for the token to reach them.
There is no real networking: everything runs as a single simulated
timeline so the ordering is deterministic to read.

Rules:
    - The token grants exclusive access; there is only ever one token.
    - A process holding the token either uses the resource for a few
      rounds and then passes the token on, or - if it doesn't need the
      resource right now - passes it on immediately.
    - The token always moves to (pid + 1) % n, regardless of use.

Usage:
    python token_ring.py [n] [rounds]
    (missing arguments are asked interactively)

Example:
    python token_ring.py 4 15
"""

import sys
import random
import time

STEP_DELAY = 0.3  # seconds between printed steps, so it reads like a live trace


def read_int(prompt, arg_value, default):
    if arg_value is not None:
        return int(arg_value)
    raw = input(prompt).strip()
    return int(raw) if raw else default


def main():
    n = read_int("Numero de procesos (default 4): ", sys.argv[1] if len(sys.argv) > 1 else None, 4)
    rounds = read_int("Numero de pasadas del token a simular (default 15): ", sys.argv[2] if len(sys.argv) > 2 else None, 15)

    token_holder = 0
    stats = {pid: {"passes": 0, "uses": 0} for pid in range(n)}

    print("=== Simulacion de Exclusion Mutua - Token Ring ===")
    print(f"Procesos en el anillo: {' -> '.join(f'P{i}' for i in range(n))} -> P0 -> ...")
    print(f"Pasos a simular: {rounds}")
    print("Solo quien tiene el token puede usar el recurso compartido.\n")

    for step in range(1, rounds + 1):
        pid = token_holder
        stats[pid]["passes"] += 1
        wants_resource = random.random() < 0.5

        print(f"--- Paso {step}: token en P{pid} ---")
        if wants_resource:
            hold_time = random.randint(1, 2)
            stats[pid]["uses"] += 1
            print(f"  [P{pid}] tiene el token y NECESITA el recurso -> entra a la region critica")
            for t in range(hold_time):
                print(f"  [P{pid}] usando el recurso... ({t + 1}/{hold_time})")
                time.sleep(STEP_DELAY)
            print(f"  [P{pid}] termino, sale de la region critica")
        else:
            print(f"  [P{pid}] tiene el token pero no necesita el recurso ahora")

        next_pid = (pid + 1) % n
        print(f"  [P{pid}] --TOKEN--> P{next_pid}\n")
        token_holder = next_pid
        time.sleep(STEP_DELAY)

    print("=== Resumen ===")
    for pid in range(n):
        print(f"  P{pid}: recibio el token {stats[pid]['passes']} veces, "
              f"lo uso para acceder al recurso {stats[pid]['uses']} veces")
    print("\nExclusion mutua garantizada: el recurso solo se usa cuando se tiene el token,")
    print("y en todo momento existe un unico token circulando por el anillo.")


if __name__ == "__main__":
    main()
