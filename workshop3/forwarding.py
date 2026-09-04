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

address, hops = resolve("A")
print("Final address:", address)
print("Number of hops:", hops)