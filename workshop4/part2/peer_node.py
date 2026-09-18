"""
Workshop 4 - Part 2: Global Time without a UTC Server

Cada nodo mantiene su PROPIO reloj (no hay servidor UTC central):

    reloj_logico = time.time() + drift + offset

  * drift  -> desviacion "fisica" que se le inyecta al nodo cada k ciclos
              (simula un cristal que adelanta o atrasa)
  * offset -> correccion que el algoritmo aplica para acercarse al
              tiempo global

En cada ciclo el nodo:
  1. pregunta la hora a todos sus peers (socket REQ, con timeout),
  2. promedia las respuestas junto con su propia hora,
  3. ajusta su offset hacia esa media  ->  offset += (media - propia)

Al mismo tiempo, un hilo servidor (socket REP) responde la hora local
a los peers que se la pidan. Threading + ZMQ = peers en paralelo.

Validacion de entrada y manejo de excepciones incluidos: puertos,
direcciones de peers, parametros numericos, timeouts, respuestas
corruptas y Ctrl+C.

Usage:
    python peer_node.py <name> <port> <peer1:port,peer2:port,...> [options]

Options (key=value):
    cycles=<n>        numero de ciclos a ejecutar (0 = infinito, default 10)
    interval=<segs>   duracion de cada ciclo               (default 2.0)
    k=<n>             cada cuantos ciclos se inyecta drift (default 3)
    drift=<segs>      magnitud maxima del drift aleatorio  (default 1.5)
    seed=<n>          semilla para reproducir el experimento

Example:
    python peer_node.py A 6001 localhost:6002,localhost:6003 cycles=12 k=3
"""

import random
import sys
import threading
import time

import zmq

TIME_REQUEST = "TIME"
RECV_TIMEOUT_MS = 1500        # espera maxima por la respuesta de un peer
SERVER_POLL_MS = 500          # cada cuanto revisa el hilo servidor si debe parar
MAX_MESSAGE_BYTES = 256
# Un reloj no puede estar a mas de esto de nuestra hora: filtra respuestas absurdas
MAX_PLAUSIBLE_SKEW_S = 3600.0


# ----------------------------------------------------------------------
# Validacion de entrada
# ----------------------------------------------------------------------
def validate_name(value):
    """El nombre del nodo: no vacio, corto y sin espacios (va dentro del mensaje)."""
    if value is None or not str(value).strip():
        raise ValueError("Node name cannot be empty")
    name = str(value).strip()
    if len(name) > 32:
        raise ValueError(f"Node name too long ({len(name)} chars, max 32)")
    if any(c.isspace() for c in name):
        raise ValueError(f"Node name '{name}' cannot contain spaces")
    return name


def validate_port(value):
    """Valida un puerto TCP y lo devuelve como int en 1..65535."""
    try:
        port = int(str(value).strip())
    except (TypeError, ValueError, AttributeError):
        raise ValueError(f"Port must be an integer, got '{value}'")
    if not 1 <= port <= 65535:
        raise ValueError(f"Port must be in range 1-65535, got {port}")
    return port


def validate_peers(value, own_port=None):
    """
    Convierte 'host:puerto,host:puerto' en una lista de endpoints ZMQ.
    Rechaza formatos malos, duplicados y auto-referencias.
    """
    if value is None or not str(value).strip():
        raise ValueError("At least one peer is required (host:port,host:port)")

    peers = []
    for raw in str(value).split(","):
        item = raw.strip()
        if not item:
            continue
        if ":" not in item:
            raise ValueError(f"Peer '{item}' must have the form host:port")
        host, _, port_str = item.rpartition(":")
        host = host.strip()
        if not host:
            raise ValueError(f"Peer '{item}' has an empty host")
        port = validate_port(port_str)
        if own_port is not None and port == own_port and host in ("localhost", "127.0.0.1", "*"):
            raise ValueError(f"Peer '{item}' points to this same node (port {own_port})")
        endpoint = f"tcp://{host}:{port}"
        if endpoint in peers:
            raise ValueError(f"Duplicated peer '{item}'")
        peers.append(endpoint)

    if not peers:
        raise ValueError("Peer list is empty after parsing")
    return peers


def validate_number(value, name, minimum, maximum, cast=float):
    """Valida un parametro numerico dentro de un rango cerrado."""
    try:
        number = cast(str(value).strip())
    except (TypeError, ValueError, AttributeError):
        raise ValueError(f"{name} must be a number, got '{value}'")
    if not minimum <= number <= maximum:
        raise ValueError(f"{name} must be in range [{minimum}, {maximum}], got {number}")
    return number


def parse_reply(raw, own_time):
    """
    Valida la respuesta de un peer: '<nombre> <timestamp>'.
    Devuelve (nombre, timestamp) o lanza ValueError.
    """
    if not raw:
        raise ValueError("empty reply")
    if len(raw) > MAX_MESSAGE_BYTES:
        raise ValueError(f"reply too large ({len(raw)} bytes)")
    try:
        text = raw.decode("utf-8").strip()
    except UnicodeDecodeError:
        raise ValueError("reply is not valid UTF-8")

    parts = text.split()
    if len(parts) != 2:
        raise ValueError(f"malformed reply '{text}' (expected name + timestamp)")

    peer_name, stamp = parts
    try:
        peer_time = float(stamp)
    except ValueError:
        raise ValueError(f"timestamp '{stamp}' is not a number")
    if peer_time <= 0:
        raise ValueError(f"timestamp {peer_time} is not positive")
    if abs(peer_time - own_time) > MAX_PLAUSIBLE_SKEW_S:
        raise ValueError(f"timestamp from '{peer_name}' is {peer_time - own_time:+.1f}s "
                         f"away from ours; discarded as implausible")
    return peer_name, peer_time


def fmt(ts):
    """Formatea un timestamp como HH:MM:SS.mmm (hora local del reloj logico)."""
    return time.strftime("%H:%M:%S", time.localtime(ts)) + f".{int((ts % 1) * 1000):03d}"


# ----------------------------------------------------------------------
# Nodo
# ----------------------------------------------------------------------
class PeerNode:
    """Un peer con reloj propio, hilo servidor y algoritmo de promediado."""

    def __init__(self, name, port, peers, cycles=10, interval=2.0,
                 k=3, drift_max=1.5, seed=None):
        self.name = validate_name(name)
        self.port = validate_port(port)
        self.peers = validate_peers(peers, own_port=self.port)
        self.cycles = int(validate_number(cycles, "cycles", 0, 10000, int))
        self.interval = validate_number(interval, "interval", 0.1, 600.0, float)
        self.k = int(validate_number(k, "k", 1, 1000, int))
        self.drift_max = validate_number(drift_max, "drift", 0.0, 3600.0, float)

        self._rng = random.Random(None if seed is None else int(seed))
        self._lock = threading.Lock()
        self._drift = 0.0        # desviacion fisica inyectada
        self._offset = 0.0       # correccion calculada por el algoritmo
        self._stop = threading.Event()
        self._context = zmq.Context.instance()
        self._server_thread = None

    # ---------------- reloj logico ----------------
    def local_time(self):
        """Hora que este nodo cree que es (su vision del tiempo global)."""
        with self._lock:
            return time.time() + self._drift + self._offset

    def adjust(self, delta):
        """Aplica una correccion al reloj logico."""
        with self._lock:
            self._offset += delta

    def inject_drift(self):
        """Mete drift aleatorio (simula imprecision del cristal). Devuelve el delta."""
        delta = self._rng.uniform(-self.drift_max, self.drift_max)
        with self._lock:
            self._drift += delta
        return delta

    def preset_skew(self, seconds):
        """Desincroniza el reloj antes de arrancar (cada nodo parte distinto)."""
        with self._lock:
            self._drift += float(seconds)

    def skew(self):
        """Desviacion total del reloj logico respecto al reloj real del SO."""
        with self._lock:
            return self._drift + self._offset

    # ---------------- hilo servidor (REP) ----------------
    def _serve(self):
        socket = self._context.socket(zmq.REP)
        socket.setsockopt(zmq.LINGER, 0)
        try:
            socket.bind(f"tcp://*:{self.port}")
        except zmq.ZMQError as exc:
            print(f"[{self.name}] [ERROR] Cannot bind port {self.port}: {exc}")
            socket.close(linger=0)
            self._stop.set()
            return

        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)
        try:
            while not self._stop.is_set():
                try:
                    if not dict(poller.poll(SERVER_POLL_MS)):
                        continue
                    raw = socket.recv()
                except zmq.ZMQError as exc:
                    if not self._stop.is_set():
                        print(f"[{self.name}] [ERROR] Server receive failed: {exc}")
                    break

                # Se responde SIEMPRE: si no, el socket REP queda bloqueado
                try:
                    if len(raw) > MAX_MESSAGE_BYTES:
                        raise ValueError("request too large")
                    text = raw.decode("utf-8").strip().upper()
                    if text != TIME_REQUEST:
                        raise ValueError(f"unknown request '{text}'")
                    socket.send_string(f"{self.name} {self.local_time():.6f}")
                except (ValueError, UnicodeDecodeError) as exc:
                    print(f"[{self.name}] [WARN] Rejected request: {exc}")
                    try:
                        socket.send_string(f"ERROR {exc}")
                    except zmq.ZMQError:
                        break
                except zmq.ZMQError as exc:
                    print(f"[{self.name}] [ERROR] Server send failed: {exc}")
                    break
        finally:
            socket.close(linger=0)

    def start_server(self):
        self._server_thread = threading.Thread(
            target=self._serve, name=f"{self.name}-server", daemon=True)
        self._server_thread.start()

    # ---------------- cliente: pedir hora a un peer ----------------
    def ask_peer(self, endpoint):
        """
        Pide la hora a un peer. Devuelve (nombre, hora_estimada) o None.
        La hora se compensa con RTT/2 (Cristian): el peer respondio en el
        pasado, asi que su reloj ya avanzo mientras el mensaje volvia.
        """
        socket = self._context.socket(zmq.REQ)
        socket.setsockopt(zmq.RCVTIMEO, RECV_TIMEOUT_MS)
        socket.setsockopt(zmq.LINGER, 0)
        try:
            socket.connect(endpoint)
            t0 = time.time()
            socket.send_string(TIME_REQUEST)
            raw = socket.recv()
            rtt = time.time() - t0
            peer_name, peer_time = parse_reply(raw, self.local_time())
            return peer_name, peer_time + rtt / 2.0
        except zmq.Again:
            print(f"[{self.name}] [WARN] Peer {endpoint} did not answer in "
                  f"{RECV_TIMEOUT_MS} ms (ignored this cycle)")
        except zmq.ZMQError as exc:
            print(f"[{self.name}] [WARN] Peer {endpoint} unreachable: {exc}")
        except ValueError as exc:
            print(f"[{self.name}] [WARN] Bad reply from {endpoint}: {exc}")
        finally:
            socket.close(linger=0)
        return None

    # ---------------- algoritmo ----------------
    def run(self, stop_when_done=True):
        """
        Ejecuta los ciclos de sincronizacion. Devuelve el skew final.

        stop_when_done=False deja el hilo servidor vivo al terminar los
        ciclos: los peers que todavia esten sincronizando siguen recibiendo
        respuesta en vez de comerse un timeout. Quien lo llama asi se
        encarga de invocar stop() despues (ver run_peers.py).
        """
        self.start_server()
        time.sleep(0.3)   # dar tiempo a que todos los peers hagan bind

        print(f"[{self.name}] Peer node on port {self.port} | peers: "
              f"{', '.join(self.peers)} | drift every k={self.k} cycles "
              f"(max {self.drift_max:.2f}s)")

        cycle = 0
        try:
            while not self._stop.is_set():
                cycle += 1

                # 1) Drift aleatorio cada k ciclos
                if cycle % self.k == 0 and self.drift_max > 0:
                    delta = self.inject_drift()
                    print(f"[{self.name}] cycle {cycle}: DRIFT injected "
                          f"{delta:+.3f}s -> clock {fmt(self.local_time())}")

                # 2) Preguntar la hora a los peers
                own_time = self.local_time()
                samples = [own_time]
                detail = [f"self={fmt(own_time)}"]
                for endpoint in self.peers:
                    answer = self.ask_peer(endpoint)
                    if answer is None:
                        continue
                    peer_name, peer_time = answer
                    samples.append(peer_time)
                    detail.append(f"{peer_name}={fmt(peer_time)} "
                                  f"({peer_time - own_time:+.3f}s)")

                # 3) Promediar y ajustar
                if len(samples) == 1:
                    print(f"[{self.name}] cycle {cycle}: no peer answered, "
                          f"clock left untouched at {fmt(own_time)}")
                else:
                    average = sum(samples) / len(samples)
                    correction = average - own_time
                    self.adjust(correction)
                    print(f"[{self.name}] cycle {cycle}: {' | '.join(detail)}")
                    print(f"[{self.name}] cycle {cycle}: mean={fmt(average)} "
                          f"from {len(samples)} clocks -> adjust {correction:+.3f}s "
                          f"| new clock {fmt(self.local_time())} "
                          f"(skew vs OS {self.skew():+.3f}s)")

                if self.cycles and cycle >= self.cycles:
                    break
                self._stop.wait(self.interval)
        except KeyboardInterrupt:
            print(f"\n[{self.name}] Stopped by user.")
            self.stop()
        except Exception:
            self.stop()          # ante un fallo inesperado no dejamos el servidor colgado
            raise
        else:
            if stop_when_done:
                self.stop()

        print(f"[{self.name}] FINAL clock {fmt(self.local_time())} "
              f"| skew vs OS clock {self.skew():+.3f}s")
        return self.skew()

    def stop(self):
        self._stop.set()
        if self._server_thread is not None:
            self._server_thread.join(timeout=2.0)


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def parse_options(argv):
    """Convierte los argumentos key=value en un diccionario validado."""
    allowed = {"cycles", "interval", "k", "drift", "seed"}
    options = {}
    for item in argv:
        if "=" not in item:
            raise ValueError(f"Option '{item}' must have the form key=value")
        key, _, value = item.partition("=")
        key = key.strip().lower()
        if key not in allowed:
            raise ValueError(f"Unknown option '{key}' (allowed: {', '.join(sorted(allowed))})")
        if key in options:
            raise ValueError(f"Option '{key}' given twice")
        options[key] = value.strip()
    return options


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        print("[ERROR] Missing arguments: <name> <port> <peers>")
        return 2

    try:
        options = parse_options(sys.argv[4:])
        node = PeerNode(
            name=sys.argv[1],
            port=sys.argv[2],
            peers=sys.argv[3],
            cycles=options.get("cycles", 10),
            interval=options.get("interval", 2.0),
            k=options.get("k", 3),
            drift_max=options.get("drift", 1.5),
            seed=options.get("seed"),
        )
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        return 2

    node.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
