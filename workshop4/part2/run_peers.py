"""
Workshop 4 - Part 2: lanzador de peers en paralelo

Levanta N nodos PeerNode en hilos separados (cada uno con su propio
socket REP, su propio reloj y su propio drift) para poder ver toda la
simulacion en una sola consola.

Los relojes arrancan DESINCRONIZADOS a proposito: a cada nodo se le
mete un skew inicial aleatorio, y despues el algoritmo de promediado
deberia hacerlos converger.

Usage:
    python run_peers.py [options]

Options (key=value):
    peers=<n>        numero de nodos            (default 3, max 10)
    cycles=<n>       ciclos por nodo            (default 8)
    interval=<segs>  duracion del ciclo         (default 1.0)
    k=<n>            drift cada k ciclos        (default 3)
    drift=<segs>     magnitud maxima del drift  (default 1.5)
    spread=<segs>    desincronizacion inicial   (default 6.0)
    base_port=<n>    primer puerto a usar       (default 6001)
    seed=<n>         semilla reproducible

Example:
    python run_peers.py peers=3 cycles=8 k=3 drift=1.5 seed=7
"""

import random
import sys
import threading
import time

from peer_node import PeerNode, fmt, validate_number, validate_port

NAMES = "ABCDEFGHIJ"


def build_nodes(n, base_port, cycles, interval, k, drift_max, spread, rng, seed):
    """Crea los N nodos, cada uno conociendo a todos los demas."""
    ports = [base_port + i for i in range(n)]
    for port in ports:
        validate_port(port)          # el ultimo puerto tambien debe ser valido

    nodes = []
    for i in range(n):
        peer_list = ",".join(f"localhost:{p}" for p in ports if p != ports[i])
        node = PeerNode(
            name=NAMES[i], port=ports[i], peers=peer_list,
            cycles=cycles, interval=interval, k=k, drift_max=drift_max,
            seed=None if seed is None else int(seed) + i,
        )
        node.preset_skew(rng.uniform(-spread / 2.0, spread / 2.0))
        nodes.append(node)
    return nodes


def snapshot(nodes):
    """Lee el reloj logico de todos los nodos casi al mismo tiempo."""
    return [(node.name, node.local_time(), node.skew()) for node in nodes]


def print_table(title, rows):
    print(f"\n{title}")
    print(f"  {'node':<6}{'clock':<16}{'skew vs OS':>12}")
    for name, clock, skew in rows:
        print(f"  {name:<6}{fmt(clock):<16}{skew:>+11.3f}s")
    times = [clock for _, clock, _ in rows]
    print(f"  spread (max-min) = {max(times) - min(times):.3f}s")


def main():
    try:
        options = parse_options_run(sys.argv[1:])
        n = int(validate_number(options.get("peers", 3), "peers", 2, len(NAMES), int))
        cycles = int(validate_number(options.get("cycles", 8), "cycles", 1, 1000, int))
        interval = validate_number(options.get("interval", 1.0), "interval", 0.1, 60.0, float)
        k = int(validate_number(options.get("k", 3), "k", 1, 100, int))
        drift_max = validate_number(options.get("drift", 1.5), "drift", 0.0, 60.0, float)
        spread = validate_number(options.get("spread", 6.0), "spread", 0.0, 600.0, float)
        base_port = int(validate_number(options.get("base_port", 6001), "base_port", 1024, 65000, int))
        seed = options.get("seed")
        if seed is not None:
            seed = int(validate_number(seed, "seed", 0, 2 ** 31, int))

        rng = random.Random(seed)
        nodes = build_nodes(n, base_port, cycles, interval, k, drift_max, spread, rng, seed)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        print(__doc__)
        return 2

    print(f"Part 2 - Global time without UTC server: {n} peers, {cycles} cycles, "
          f"interval {interval}s, drift every k={k} cycles (max {drift_max}s)")

    before = snapshot(nodes)
    print_table("BEFORE synchronization:", before)
    print()

    # stop_when_done=False: al acabar sus ciclos el nodo deja vivo su hilo
    # servidor, para que los peers que aun sincronizan no se coman un timeout.
    # El apagado real lo hace el lanzador cuando todos terminaron.
    threads = [threading.Thread(target=node.run, args=(False,), name=f"peer-{node.name}")
               for node in nodes]
    try:
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n[launcher] Ctrl+C: stopping all peers...")
    finally:
        for node in nodes:
            node.stop()
        for t in threads:
            t.join(timeout=3.0)

    time.sleep(0.2)
    after = snapshot(nodes)
    print_table("AFTER synchronization:", after)

    spread_before = max(t for _, t, _ in before) - min(t for _, t, _ in before)
    spread_after = max(t for _, t, _ in after) - min(t for _, t, _ in after)
    if spread_before > 0:
        reduction = 100 * (1 - spread_after / spread_before)
        print(f"\nConvergence: spread {spread_before:.3f}s -> {spread_after:.3f}s "
              f"({reduction:.1f}% closer)")
    else:
        print(f"\nConvergence: final spread {spread_after:.3f}s")
    return 0


def parse_options_run(argv):
    """Igual que parse_options del nodo, pero con las claves del lanzador."""
    allowed = {"peers", "cycles", "interval", "k", "drift", "spread", "base_port", "seed"}
    options = {}
    for item in argv:
        if "=" not in item:
            raise ValueError(f"Option '{item}' must have the form key=value")
        key, _, value = item.partition("=")
        key = key.strip().lower()
        if key not in allowed:
            raise ValueError(f"Unknown option '{key}' (allowed: {', '.join(sorted(allowed))})")
        if key in options:
            raise ValueError(f"Option '{key}' given twice")
        options[key] = value.strip()
    return options


if __name__ == "__main__":
    sys.exit(main())
