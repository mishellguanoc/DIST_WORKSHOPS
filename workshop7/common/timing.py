"""Stage timing and HTTP size measurements."""

from time import perf_counter_ns


class StageTimer:
    """Records the time between consecutive laps, in milliseconds."""

    def __init__(self):
        self.stages_ms = {}
        self._last = perf_counter_ns()

    def lap(self, name):
        now = perf_counter_ns()
        self.stages_ms[name] = (now - self._last) / 1e6
        self._last = now

    def server_timing(self):
        """Format the stages as an HTTP Server-Timing header value."""
        stages = {**self.stages_ms, "total": sum(self.stages_ms.values())}
        return ", ".join(f"{name};dur={ms:.3f}" for name, ms in stages.items())


def parse_server_timing(header):
    """Turn a Server-Timing header value into {stage: milliseconds}."""
    stages = {}
    for item in filter(None, header.split(",")):
        name, _, duration = item.strip().partition(";dur=")
        stages[name] = float(duration)
    return stages


def _headers_size(raw_headers):
    # Each header is "name: value\r\n", and a blank line ends the block.
    return sum(len(name) + len(value) + 4 for name, value in raw_headers) + 2


def request_wire_bytes(request):
    """Return (HTTP head size, body size); TCP/IP overhead is not included."""
    start_line = f"{request.method} {request.url.raw_path.decode()} HTTP/1.1\r\n"
    return len(start_line) + _headers_size(request.headers.raw), len(request.content)


def response_wire_bytes(response):
    """Return (HTTP head size, body size); TCP/IP overhead is not included."""
    start_line = f"HTTP/1.1 {response.status_code} {response.reason_phrase}\r\n"
    return len(start_line) + _headers_size(response.headers.raw), len(response.content)


def describe_cost(result):
    """Return the size and time lines printed by both clients."""
    request_head, request_body = result["request_bytes"]
    response_head, response_body = result["response_bytes"]
    return (
        f"bytes: request {request_head}+{request_body}, "
        f"response {response_head}+{response_body} (HTTP head + JSON body)",
        f"time: RTT {result['client_ms']['rtt']:.3f} ms, "
        f"server {result['server_ms'].get('total', 0):.3f} ms",
    )
