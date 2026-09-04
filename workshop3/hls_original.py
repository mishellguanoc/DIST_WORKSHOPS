tree = {
    "ROOT": {
        "AMERICA": {
            "ECUADOR": {
                "IBARRA": {},
                "QUITO": {}
            },
            "USA": {}
        },
        "EUROPE": {}
    }
}

entities = {
    "IBARRA": {
        "server01": "10.0.1.20"
    },
    "QUITO": {
        "server02": "10.0.2.30"
    }
}

# --- Build parent map from tree ---
parent_of = {}

def build_parents(node, name, parent):
    parent_of[name] = parent
    for child_name, child_node in node.items():
        build_parents(child_node, child_name, name)

build_parents(tree["ROOT"], "ROOT", None)

# --- Upward pointers: domain -> {entity: child_domain_to_follow} ---
pointers = {}

def register(entity, domain):
    """Register entity's leaf domain and propagate a downward pointer
    at every ancestor up to ROOT."""
    current = domain
    while parent_of.get(current) is not None:
        parent = parent_of[current]
        pointers.setdefault(parent, {})[entity] = current
        current = parent

for domain, ents in entities.items():
    for entity in ents:
        register(entity, domain)


def lookup(entity, starting_domain):
    path = [starting_domain]
    current = starting_domain

    # 1. Check locally at the starting leaf
    if entity in entities.get(current, {}):
        path.append(entity)
        return entities[current][entity], path

    # 2. Move upward until a pointer to the entity is found, or ROOT is reached
    while current != "ROOT":
        current = parent_of[current]
        path.append(current)
        if entity in pointers.get(current, {}):
            # 3. Follow downward pointers to the leaf holding the entity
            while entity in pointers.get(current, {}):
                current = pointers[current][entity]
                path.append(current)
            if entity in entities.get(current, {}):
                path.append(entity)
                return entities[current][entity], path

    return None, path


def run_lookup(entity, starting_domain):
    address, path = lookup(entity, starting_domain)
    print(" -> ".join(path))
    if address:
        print("Resolved address:", address)
    else:
        print("Entity not found")
    print()


print("=== Before moving any entity ===\n")
run_lookup("server01", "IBARRA")
run_lookup("server02", "IBARRA")
run_lookup("server99", "IBARRA")
