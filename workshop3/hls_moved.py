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

parent_of = {}

def build_parents(node, name, parent):
    parent_of[name] = parent
    for child_name, child_node in node.items():
        build_parents(child_node, child_name, name)

build_parents(tree["ROOT"], "ROOT", None)

pointers = {}

def register(entity, domain):
    current = domain
    while parent_of.get(current) is not None:
        parent = parent_of[current]
        pointers.setdefault(parent, {})[entity] = current
        current = parent

def unregister(entity, domain):
    """Remove entity's leaf record and all upward pointers that point to it."""
    current = domain
    while parent_of.get(current) is not None:
        parent = parent_of[current]
        if pointers.get(parent, {}).get(entity) == current:
            del pointers[parent][entity]
        current = parent

for domain, ents in entities.items():
    for entity in ents:
        register(entity, domain)


def lookup(entity, starting_domain):
    path = [starting_domain]
    current = starting_domain

    if entity in entities.get(current, {}):
        path.append(entity)
        return entities[current][entity], path

    while current != "ROOT":
        current = parent_of[current]
        path.append(current)
        if entity in pointers.get(current, {}):
            while entity in pointers.get(current, {}):
                current = pointers[current][entity]
                path.append(current)
            if entity in entities.get(current, {}):
                path.append(entity)
                return entities[current][entity], path

    return None, path


def move_entity(entity, old_domain, new_domain):
    address = entities[old_domain].pop(entity)
    unregister(entity, old_domain)
    entities.setdefault(new_domain, {})[entity] = address
    register(entity, new_domain)


def run_lookup(entity, starting_domain):
    address, path = lookup(entity, starting_domain)
    print(" -> ".join(path))
    if address:
        print("Resolved address:", address)
    else:
        print("Entity not found")
    print()


print("=== Lookup before the move ===\n")
run_lookup("server01", "IBARRA")

print("=== Moving server01 from IBARRA to QUITO ===\n")
move_entity("server01", "IBARRA", "QUITO")

print("=== Lookup after the move ===\n")
run_lookup("server01", "IBARRA")
