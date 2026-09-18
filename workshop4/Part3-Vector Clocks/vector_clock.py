"""
Vector Clocks - Part 3 of Workshop 4 - Distributed Systems

Pure logic for vector clocks: no networking, no I/O. A clock is simply a
list of integers indexed by process id. Reused by simulation.py.

Rules:
    - Local event or send: increment your own position.
    - Receive: take the elementwise max with the received clock, then
      increment your own position.

Usage (self-test only):
    python vector_clock.py
"""


def new_clock(n):
    return [0] * n


def tick(clock, pid):
    clock[pid] += 1
    return clock


def merge(clock, received):
    for i in range(len(clock)):
        clock[i] = max(clock[i], received[i])
    return clock


def compare_clocks(v1, v2):
    le = all(a <= b for a, b in zip(v1, v2))
    ge = all(a >= b for a, b in zip(v1, v2))
    if le and ge:
        return "equal"
    if le:
        return "before"
    if ge:
        return "after"
    return "concurrent"


def format_clock(clock):
    return str(clock)


if __name__ == "__main__":
    # Self-test: build a small P0 -> P1 causal chain plus a concurrent pair.
    a = tick(new_clock(3), 0)                 # P0 local event -> [1, 0, 0]
    b = tick(new_clock(3), 1)                 # P1 local event -> [0, 1, 0], concurrent with a
    c = tick(merge(new_clock(3), a), 1)       # P1 receives a's clock -> [1, 1, 0], after a

    print("a =", format_clock(a))
    print("b =", format_clock(b))
    print("c =", format_clock(c))

    print("compare(a, c) =", compare_clocks(a, c))   # before
    print("compare(c, a) =", compare_clocks(c, a))   # after
    print("compare(a, b) =", compare_clocks(a, b))   # concurrent

    assert compare_clocks(a, c) == "before"
    assert compare_clocks(c, a) == "after"
    assert compare_clocks(a, b) == "concurrent"
    print("Self-test OK")
