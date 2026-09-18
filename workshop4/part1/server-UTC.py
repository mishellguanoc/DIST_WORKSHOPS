"""
Workshop 4 - Part 1: Coordination through a UTC Server (server side)

Servidor centralizado de tiempo: escucha peticiones en un puerto y
responde con la hora UTC del sistema.

Se agrego validacion de entrada y manejo de excepciones:
  - el puerto se valida (entero, rango 1-65535) antes de hacer bind
  - se validan los mensajes recibidos (no vacios, decodificables,
    tamano razonable) antes de responder
  - errores de ZMQ / bind / Ctrl+C se capturan y cierran limpiamente

Usage:
    python server-UTC.py [port]

Example:
    python server-UTC.py 5000
"""

import sys
import time

import zmq

DEFAULT_PORT = 5000
MAX_REQUEST_BYTES = 1024          # un "Time request" no deberia pesar mas
VALID_REQUESTS = ("TIME REQUEST", "TIME", "PING")


def validate_port(value, default=DEFAULT_PORT):
    """
    Valida un puerto TCP. Acepta str o int y devuelve un int en 1..65535.
    Lanza ValueError si el valor no es utilizable.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return default
    try:
        port = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(f"Port must be an integer, got '{value}'")
    if not 1 <= port <= 65535:
        raise ValueError(f"Port must be in range 1-65535, got {port}")
    if port < 1024:
        print(f"[WARN] Port {port} is privileged; it may require admin rights.")
    return port


def validate_request(raw):
    """
    Valida el mensaje crudo recibido del cliente.
    Devuelve el texto normalizado, o lanza ValueError si es invalido.
    """
    if not raw:
        raise ValueError("empty request")
    if len(raw) > MAX_REQUEST_BYTES:
        raise ValueError(f"request too large ({len(raw)} bytes)")
    try:
        text = raw.decode("utf-8").strip()
    except UnicodeDecodeError:
        raise ValueError("request is not valid UTF-8")
    if not text:
        raise ValueError("blank request")
    if text.upper() not in VALID_REQUESTS:
        raise ValueError(f"unknown request '{text}'")
    return text


def utc_time_server(port=DEFAULT_PORT):
    """Bucle principal REP: recibe peticiones y responde la hora UTC."""
    port = validate_port(port)

    context = zmq.Context()
    socket = context.socket(zmq.REP)      # REP stands for Reply

    try:
        socket.bind(f"tcp://*:{port}")
    except zmq.ZMQError as exc:
        print(f"[ERROR] Cannot bind to port {port}: {exc}")
        socket.close(linger=0)
        context.term()
        return 1

    print(f"UTC Time Server running on port {port}... (Ctrl+C to stop)")

    try:
        while True:
            # Wait for next request from client
            try:
                message = socket.recv()
            except zmq.ZMQError as exc:
                print(f"[ERROR] Receive failed: {exc}")
                break

            try:
                text = validate_request(message)
            except ValueError as exc:
                # Con REP hay que responder SIEMPRE, si no la maquina de
                # estados del socket queda bloqueada para el siguiente cliente.
                print(f"[WARN] Rejected request: {exc}")
                socket.send_string(f"ERROR: {exc}")
                continue

            print(f"Received request: {text}")

            # Get UTC time
            utc_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

            try:
                socket.send_string(utc_time)
            except zmq.ZMQError as exc:
                print(f"[ERROR] Send failed: {exc}")
                break

            print(f"Sent UTC time: {utc_time}")
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    finally:
        socket.close(linger=0)
        context.term()
    return 0


def main():
    try:
        port = validate_port(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PORT)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        return 2
    return utc_time_server(port)


if __name__ == "__main__":
    sys.exit(main())
