M = 5
RING_SIZE = 2 ** M

nodes = [1, 4, 9, 11, 14, 18, 20, 21, 28]


def successor(key):
    for node in nodes:
        if node >= key:
            return node
    return nodes[0]


def finger_table(node):
    table = []
    for i in range(M):
        start = (node + 2 ** i) % RING_SIZE
        target = successor(start)
        table.append((i + 1, start, target))
    return table


def in_interval(x, a, b):
    a %= RING_SIZE
    b %= RING_SIZE
    x %= RING_SIZE
    if a < b:
        return a < x < b
    return x > a or x < b


def lookup(key, start_node):
    path = [start_node]
    current = start_node
    while True:
        succ = finger_table(current)[0][2]
        if key % RING_SIZE == succ or in_interval(key, current, succ):
            path.append(succ)
            return path
        next_node = current
        for _, _, target in reversed(finger_table(current)):
            if in_interval(target, current, key):
                next_node = target
                break
        if next_node == current:
            path.append(succ)
            return path
        path.append(next_node)
        current = next_node


def print_lookup(key, start_node):
    path = lookup(key, start_node)
    print(f"Lookup key {key}")
    print(path[0])
    for node in path[1:-1]:
        print(f"-> {node}")
    print(f"-> successor({key}) = {path[-1]}")
    print(f"Total hops = {len(path) - 1}")


if __name__ == "__main__":
    keys = [3, 8, 12, 19, 26, 30]
    for key in keys:
        print(f"Key: {key} -> node: {successor(key)}")

    print()
    print("Node 1")
    for entry in finger_table(1):
        print(entry)

    print()
    for node in nodes:
        print(f"Node {node}")
        print("i    start    successor")
        for i, start, target in finger_table(node):
            print(f"{i}    {start}    {target}")
        print()

    print_lookup(26, 1)
    print()
    print_lookup(12, 28)
