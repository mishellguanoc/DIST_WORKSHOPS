"""
Publisher-Subscriber con LDAP - Workshop 3 Part 2 (Special Activity)
Adaptado del Publisher-Subscriber original (Workshop 2, Part 4)

Cada publisher, ademas de anunciar su topic por ZMQ como antes, se
REGISTRA en el directorio LDAP (ou=Services,dc=maki,dc=com) con su
IP y puerto reales, para que el subscriber pueda descubrirlo por
nombre de servicio en vez de necesitar la direccion de antemano.

Usage:
    python publisher.py <service_name> [host] [port]

Example:
    python publisher.py WEATHER 0.0.0.0 15001
    python publisher.py STOCKS  0.0.0.0 15002
    python publisher.py NEWS    0.0.0.0 15003
"""

import zmq
import time
import sys
import random
import socket
import ldap
import ldap.modlist as modlist


NEWS_HEADLINES = [
    "Local team wins championship",
    "New tech breakthrough announced",
    "Markets react to policy change",
    "City council approves new budget",
    "Scientists discover new species",
]

# ---------------- Configuracion LDAP ----------------
LDAP_SERVER = "ldap://localhost"
ADMIN_DN = "cn=admin,dc=maki,dc=com"
ADMIN_PASSWORD = "introduce_password"   # The password of the dpkg-reconfigure slapd
BASE_SERVICES = "ou=Services,dc=maki,dc=com"


def build_payload(service):
    """
    Builds message content appropriate for the given service/topic.
    Falls back to a generic random value for unknown services.
    """
    if service == "WEATHER":
        temperature = round(random.uniform(-5, 40), 1)
        humidity = random.randint(20, 100)
        return f"temperature={temperature}C humidity={humidity}%"
    elif service == "STOCKS":
        price = round(random.uniform(10, 500), 2)
        change = round(random.uniform(-5, 5), 2)
        return f"price={price} change={change:+.2f}"
    elif service == "NEWS":
        headline = random.choice(NEWS_HEADLINES)
        return f'headline="{headline}"'
    else:
        return f"value={random.randint(0, 100)}"


def obtener_ip_local():
    """Obtiene la IP con la que este publisher es alcanzable en la LAN."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def registrar_servicio(nombre, ip, puerto):
    """Registra (o re-registra) el servicio en ou=Services del directorio LDAP."""
    conn = ldap.initialize(LDAP_SERVER)
    conn.simple_bind_s(ADMIN_DN, ADMIN_PASSWORD)

    dn = f"cn={nombre},{BASE_SERVICES}"
    attrs = {
        "objectClass": [b"top", b"applicationProcess", b"ipHost"],
        "cn": [nombre.encode()],
        "ipHostNumber": [ip.encode()],
        "description": [str(puerto).encode()],  # el puerto se guarda en description
    }
    ldif = modlist.addModlist(attrs)

    try:
        conn.add_s(dn, ldif)
    except ldap.ALREADY_EXISTS:
        conn.delete_s(dn)
        conn.add_s(dn, ldif)
    finally:
        conn.unbind_s()

    print(f"[{nombre}] Registered in LDAP -> {ip}:{puerto}")


def main():
    if len(sys.argv) < 2:
        service = input("Enter the service/topic name this publisher offers (e.g. WEATHER): ").strip().upper()
    else:
        service = sys.argv[1].strip().upper()

    if len(sys.argv) >= 3:
        bindHost = sys.argv[2]
    else:
        bindHost = input("Enter bind host/IP [0.0.0.0]: ").strip() or "0.0.0.0"

    if len(sys.argv) >= 4:
        serverPort = int(sys.argv[3])
    else:
        try:
            serverPort = int(input("Enter port number [15000]: ") or 15000)
        except ValueError:
            serverPort = 15000

    # --- Registro en LDAP (paso nuevo de esta actividad) ---
    ip_publicada = obtener_ip_local() if bindHost == "0.0.0.0" else bindHost
    registrar_servicio(service, ip_publicada, serverPort)

    # --- A partir de aqui, exactamente la logica original del Workshop 2 ---
    context = zmq.Context()
    s = context.socket(zmq.PUB)

    p = f"tcp://{bindHost}:{serverPort}"
    s.bind(p)

    print(f"[{service}] Publisher listening on {p}")

    cont = 0
    while True:
        time.sleep(2)
        cont += 1
        payload = build_payload(service)
        msg = f"{service} {time.asctime()} - #{cont} {payload}"
        print(f"[{service}] Sending: {msg}")
        s.send_string(msg)


if __name__ == "__main__":
    main()
