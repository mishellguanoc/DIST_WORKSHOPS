"""
Publisher-Subscriber con LDAP - Workshop 3 Part 2 (Special Activity)
Adaptado del Publisher-Subscriber original (Workshop 2, Part 4)

En vez de recibir manualmente las direcciones host:port de cada
publisher, el subscriber RESUELVE cada topic contra el directorio
LDAP (ou=Services,dc=maki,dc=com) para obtener la IP y el puerto
actuales del publisher que ofrece ese servicio.

Usage:
    python subscriber.py <topic1,topic2,...>

Example (subscribe to WEATHER and STOCKS, resolviendo sus
direcciones automaticamente via LDAP):
    python subscriber.py WEATHER,STOCKS
"""

import zmq
import sys
import ldap


# ---------------- Configuracion LDAP ----------------
LDAP_SERVER = "ldap://localhost"
BASE_SERVICES = "ou=Services,dc=maki,dc=com"


def resolver_servicio(nombre):
    """Busca en LDAP la IP y el puerto registrados para un topic/servicio."""
    conn = ldap.initialize(LDAP_SERVER)
    conn.simple_bind_s()  # bind anonimo, solo lectura

    filtro = f"(cn={nombre})"
    resultado = conn.search_s(BASE_SERVICES, ldap.SCOPE_SUBTREE, filtro,
                               ["ipHostNumber", "description"])
    conn.unbind_s()

    if not resultado:
        raise LookupError(f"Service '{nombre}' not found in LDAP directory")

    _dn, attrs = resultado[0]
    ip = attrs["ipHostNumber"][0].decode()
    puerto = int(attrs["description"][0].decode())
    return ip, puerto


def main():
    if len(sys.argv) >= 2:
        topics = [t.strip().upper() for t in sys.argv[1].split(",")]
    else:
        topics_str = input("Topics to subscribe to (comma separated, e.g. WEATHER,STOCKS): ")
        topics = [t.strip().upper() for t in topics_str.split(",") if t.strip()]

    # --- Resolucion de direcciones via LDAP (reemplaza el input manual) ---
    targets = []
    for topic in topics:
        ip, puerto = resolver_servicio(topic)
        targets.append(f"{ip}:{puerto}")
        print(f"[{topic}] Resolved via LDAP -> {ip}:{puerto}")

    # --- A partir de aqui, exactamente la logica original del Workshop 2 ---
    context = zmq.Context()
    s = context.socket(zmq.SUB)

    for target in targets:
        addr = f"tcp://{target}"
        s.connect(addr)
        print(f"Connected to publisher at {addr}")

    for topic in topics:
        s.setsockopt_string(zmq.SUBSCRIBE, topic)
        print(f"Subscribed to topic '{topic}'")

    poller = zmq.Poller()
    poller.register(s, zmq.POLLIN)

    print("Waiting for messages... (Ctrl+C to stop)\n")
    try:
        while True:
            events = dict(poller.poll())
            if s in events:
                msg = s.recv_string()
                print("Received:", msg)
    except KeyboardInterrupt:
        print("\nSubscriber stopped.")


if __name__ == "__main__":
    main()
