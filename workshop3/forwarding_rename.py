locations = {
    "A": "B",
    "B": "C",
    "C": "D",
    "D": "192.168.1.50:5000"
}

def resolve(location):
    hops = 0
    while location in locations:
        print("Following:", location, "->", locations[location])
        location = locations[location]
        hops += 1
    return location, hops


# --- Before optimization ---
print("=== Before optimization ===")
address, hops_before = resolve("A")
print("Final address:", address)
print("Number of hops:", hops_before)

# --- Shortcut / chain-reduction ---
locations["A"] = address

print("\n=== After optimization (shortcut created) ===")
address, hops_after = resolve("A")
print("Final address:", address)
print("Number of hops:", hops_after)

print(f"\nBefore optimization: {hops_before} hops")
print(f"After optimization:  {hops_after} hops")

# --- Simulate a failure ---
del locations["C"]

print("\n=== After deleting C (simulated failure) ===")
try:
    address, hops_fail = resolve("B")
    print("Final address:", address)
    print("Number of hops:", hops_fail)
except KeyError as e:
    print("Broken pointer, missing node:", e)