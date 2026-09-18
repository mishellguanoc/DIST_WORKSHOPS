"""
Vector Clocks Simulation - Part 3 of Workshop 4 - Distributed Systems

Single-process simulation of N distributed processes that each keep a
vector clock to track causality. There is no real networking: a "message"
is just an entry placed in the target process's inbox, and it gets
processed the next time that process takes its turn - which is exactly
how message passing behaves in a real distributed system (send does not
block, receive happens whenever the process gets to it).

Rules:
    - Local event or send: the process increments its own position.
    - Receive: the process merges (elementwise max) with the received
      clock, then increments its own position.

Usage:
    python simulation.py [n] [rounds]
    (missing arguments are asked interactively)

Example:
    python simulation.py 3 10
"""

import sys
import random
import time

import vector_clock as vc

STEP_DELAY = 0.4  # seconds between printed steps, so it reads like a live trace


def read_int(prompt, arg_value, default):
    if arg_value is not None:
        return int(arg_value)
    raw = input(prompt).strip()
    return int(raw) if raw else default


def decide_action(pid, seq, has_incoming):
    if has_incoming:
        return "recv"
    # First-ever turn of every process: always LOCAL. No process could have
    # received anything yet, so every process starts with a unit vector -
    # unit vectors are never comparable -> guarantees a CONCURRENT pair.
    if seq == 0:
        return "local"
    # Second turn of P0: always SEND, guaranteeing at least one real
    # message flows, so its eventual RECV is always causally AFTER it.
    if pid == 0 and seq == 1:
        return "send"
    return random.choice(["local", "send"])


def main():
    n = read_int("Numero de procesos (default 3): ", sys.argv[1] if len(sys.argv) > 1 else None, 3)
    rounds = read_int("Numero de rondas a simular (default 8): ", sys.argv[2] if len(sys.argv) > 2 else None, 8)

    clocks = [vc.new_clock(n) for _ in range(n)]
    inboxes = [[] for _ in range(n)]          # inboxes[pid] = [(sender_pid, clock_snapshot), ...]
    turn_count = [0] * n
    history = {pid: [] for pid in range(n)}   # for the causality summary at the end

    print("=== Simulacion de Relojes Vectoriales ===")
    print(f"Procesos a simular: {n} ({', '.join(f'P{i}' for i in range(n))})")
    print(f"Rondas: {rounds}  (cada proceso actua una vez por ronda)")
    print("Reglas: evento LOCAL -> incrementa el reloj propio.")
    print("        SEND         -> incrementa el reloj propio y lo adjunta al mensaje.")
    print("        RECV         -> combina (maximo) con el reloj recibido y luego incrementa el propio.")
    print()
    input("Presiona Enter para iniciar...\n")

    for round_num in range(1, rounds + 1):
        print(f"--- Ronda {round_num} ---")
        for pid in range(n):
            seq = turn_count[pid]
            has_incoming = bool(inboxes[pid])
            action = decide_action(pid, seq, has_incoming)

            if action == "recv":
                sender, msg_clock = inboxes[pid].pop(0)
                vc.merge(clocks[pid], msg_clock)
                vc.tick(clocks[pid], pid)
                print(f"  [P{pid}] <--RECV-- P{sender}   clock(P{pid}) = {vc.format_clock(clocks[pid])}")
                history[pid].append(("RECV", clocks[pid].copy(), msg_clock, f"from P{sender}"))
            elif action == "send":
                vc.tick(clocks[pid], pid)
                target = random.choice([j for j in range(n) if j != pid])
                inboxes[target].append((pid, clocks[pid].copy()))
                print(f"  [P{pid}] --SEND--> P{target}   clock(P{pid}) = {vc.format_clock(clocks[pid])}")
                history[pid].append(("SEND", clocks[pid].copy(), None, f"to P{target}"))
            else:
                vc.tick(clocks[pid], pid)
                print(f"  [P{pid}] evento LOCAL       clock(P{pid}) = {vc.format_clock(clocks[pid])}")
                history[pid].append(("LOCAL", clocks[pid].copy(), None, ""))

            turn_count[pid] += 1
            time.sleep(STEP_DELAY)
        print()

    print("=== Vectores de reloj finales ===")
    for pid in range(n):
        print(f"  P{pid}: {vc.format_clock(clocks[pid])}")

    print("\n=== Relaciones causales demostradas ===")
    print("Concurrencia (primer evento de cada proceso, ninguno pudo haber visto al otro):")
    for i in range(n):
        for j in range(i + 1, n):
            e1, e2 = history[i][0], history[j][0]
            result = vc.compare_clocks(e1[1], e2[1])
            print(f"  P{i}#1 {vc.format_clock(e1[1])}  vs  P{j}#1 {vc.format_clock(e2[1])}  -> {result}")

    print("\nCausalidad (cada RECV comparado con el reloj que trajo el mensaje):")
    any_recv = False
    for pid in range(n):
        for action, clock, msg_clock, detail in history[pid]:
            if action == "RECV":
                any_recv = True
                result = vc.compare_clocks(msg_clock, clock)
                print(f"  mensaje {vc.format_clock(msg_clock)} {detail.replace('from ', 'de ')}  -> {result} ->  P{pid} queda en {vc.format_clock(clock)}")
    if not any_recv:
        print("  (no hubo ningun RECV en esta corrida; volve a intentar con mas rondas)")


if __name__ == "__main__":
    main()
