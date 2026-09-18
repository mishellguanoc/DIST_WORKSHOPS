"""
Workshop 4 - Part 1: Coordination through a UTC Server (client side)

Cliente que pide la hora UTC al servidor centralizado y la imprime.
Lanza varios hilos (uno por peticion) para simular varios nodos
sincronizandose contra el mismo servidor.

Se agrego validacion de entrada y manejo de excepciones:
  - host y puerto se validan antes de conectar
  - timeout de recepcion: si el servidor no esta arriba, el cliente
    no se queda colgado para siempre
  - la respuesta se valida (formato de fecha UTC) antes de aceptarla
  - se corrigio el bug del codigo original: threading.Thread(target=f())
    ejecutaba la funcion en el hilo principal en vez de pasarla como
    callable; ahora es target=f y los hilos corren de verdad en paralelo

Usage:
    python client-UTC.py [host] [port] [num_clients]

Example:
    python client-UTC.py localhost 5000 3
"""

import sys
import threading

import zmq

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 5000
DEFAULT_CLIENTS = 3
RECV_TIMEOUT_MS = 5000            # 5 s de espera maxima por respuesta
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def validate_host(value, default=DEFAULT_HOST):
    """Valida el hostname/IP: no vacio y sin caracteres raros de URL."""
    if value is None or not str(value).strip():
        return default
    host = str(value).strip()
    for bad in (" ", "/", "\\", ":"):
        if bad in host:
            raise ValueError(f"Invalid host '{host}' (unexpected '{bad}')")
    return host


def validate_port(value, default=DEFAULT_PORT):
    """Valida un puerto TCP y lo devuelve como int en 1..65535."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return default
    try:
        port = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(f"Port must be an integer, got '{value}'")
    if not 1 <= port <= 65535:
        raise ValueError(f"Port must be in range 1-65535, got {port}")
    return port


def validate_count(value, default=DEFAULT_CLIENTS, maximum=50):
    """Valida el numero de clientes/hilos a lanzar."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return default
    try:
        n = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(f"Number of clients must be an integer, got '{value}'")
    if not 1 <= n <= maximum:
        raise ValueError(f"Number of clients must be in range 1-{maximum}, got {n}")
    return n


def validate_reply(raw):
    """
    Valida la respuesta del servidor: debe ser UTF-8 y tener el formato
    '%Y-%m-%d %H:%M:%S'. Devuelve el texto o lanza ValueError.
    """
    import time as _time

    if not raw:
        raise ValueError("empty reply from server")
    try:
        text = raw.decode("utf-8").strip()
    except UnicodeDecodeError:
        raise ValueError("reply is not valid UTF-8")
    if text.startswith("ERROR:"):
        raise ValueError(f"server rejected the request ({text})")
    try:
        _time.strptime(text, TIME_FORMAT)
    except ValueError:
        raise ValueError(f"reply '{text}' is not a valid UTC timestamp")
    return text


def utc_time_client(name, hostname=DEFAULT_HOST, port=DEFAULT_PORT):
    """Pide la hora UTC al servidor y la imprime. No propaga excepciones."""
    context = zmq.Context.instance()
    socket = context.socket(zmq.REQ)      # REQ stands for Request
    socket.setsockopt(zmq.RCVTIMEO, RECV_TIMEOUT_MS)
    socket.setsockopt(zmq.LINGER, 0)      # no bloquear el cierre si falla

    endpoint = f"tcp://{hostname}:{port}"
    try:
        socket.connect(endpoint)          # Connect to the server's port

        # Send a request for UTC time
        socket.send_string("Time request")

        # Receive the UTC time from the server
        utc_time = validate_reply(socket.recv())
        print(f"[{name}] Received UTC time: {utc_time}")
    except zmq.Again:
        print(f"[{name}] [ERROR] Timeout: no reply from {endpoint} "
              f"in {RECV_TIMEOUT_MS} ms. Is server-UTC.py running?")
    except zmq.ZMQError as exc:
        print(f"[{name}] [ERROR] ZMQ failure against {endpoint}: {exc}")
    except ValueError as exc:
        print(f"[{name}] [ERROR] Bad reply: {exc}")
    finally:
        socket.close(linger=0)


def main():
    try:
        hostname = validate_host(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST)
        port = validate_port(sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PORT)
        n_clients = validate_count(sys.argv[3] if len(sys.argv) > 3 else DEFAULT_CLIENTS)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        print("Usage: python client-UTC.py [host] [port] [num_clients]")
        return 2

    print(f"Requesting UTC time from tcp://{hostname}:{port} with {n_clients} client(s)\n")

    threads = []
    for ii in range(n_clients):
        t = threading.Thread(target=utc_time_client,
                             args=(f"client-{ii + 1}", hostname, port))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    zmq.Context.instance().term()
    print("Done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
