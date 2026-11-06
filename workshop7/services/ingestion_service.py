"""Activity 1: ingestion service with predefined JSON Schemas (machine B, WSL)."""

import hashlib
import json
import os
import platform
from collections import defaultdict

from fastapi import FastAPI, Request, Response

from common.timing import StageTimer
from common.validation import validate_request, validate_response

PARTITIONS = 8
# Not the hostname: WSL inherits it from Windows, so both machines share it.
MACHINE = platform.system()
QUIET = os.environ.get("W7_QUIET") == "1"

app = FastAPI(title="ingestion")

# Stands in for Redis, so the measurements isolate the cost of JSON.
sequences = defaultdict(int)


def log(text):
    if not QUIET:
        print(f"[ingestion@{MACHINE}] {text}", flush=True)


def partition_for(customer_id):
    digest = hashlib.sha256(customer_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % PARTITIONS


def ingest(message):
    partition = partition_for(message["customer_id"])
    sequences[partition] += 1
    return {
        "status": "accepted",
        "msg_id": message["msg_id"],
        "partition": partition,
        "stream": f"messages.p{partition}",
        "sequence": sequences[partition],
    }


def rejection(errors):
    return {"status": "rejected", "errors": errors}


def json_response(document, status_code, timer):
    body = json.dumps(document, separators=(",", ":")).encode("utf-8")
    timer.lap("serialize")
    return Response(
        body,
        status_code,
        media_type="application/json",
        headers={"Server-Timing": timer.server_timing()},
    )


@app.post("/webhook")
async def webhook(request: Request):
    raw = await request.body()
    timer = StageTimer()

    try:
        message = json.loads(raw)
    except ValueError as error:
        timer.lap("parse")
        answer = rejection([{"path": "$", "message": f"invalid JSON: {error}"}])
        log(f"received invalid JSON: {raw[:200]!r}")
        return json_response(answer, 400, timer)
    timer.lap("parse")

    request_errors = validate_request(message)
    timer.lap("validate_request")

    if request_errors:
        answer, status_code = rejection(request_errors), 422
    else:
        answer, status_code = ingest(message), 200
    timer.lap("handle")

    response_errors = validate_response(answer)
    timer.lap("validate_response")

    if response_errors:
        answer, status_code = rejection(response_errors), 500

    response = json_response(answer, status_code, timer)

    # Logged last so that printing is not counted in the stage timings.
    log(f"received from {request.client.host}: {raw.decode('utf-8', 'replace')}")
    log(f"request schema: {'INVALID' if request_errors else 'valid'}")
    log(f"response {status_code}: {response.body.decode('utf-8')}")
    log(f"response schema: {'INVALID' if response_errors else 'valid'}")
    return response


@app.post("/control/webhook")
async def control_webhook(request: Request):
    """Same work as /webhook without validation, to isolate the cost of the schema."""
    raw = await request.body()
    timer = StageTimer()
    message = json.loads(raw)
    timer.lap("parse")
    answer = ingest(message)
    timer.lap("handle")
    return json_response(answer, 200, timer)


@app.get("/info")
async def info(request: Request):
    return {
        "system": platform.system(),
        "release": platform.release(),
        "python": platform.python_version(),
        "client_seen_as": request.client.host,
    }


if os.environ.get("W7_FAULTS") == "1":

    @app.post("/faults/webhook")
    async def faulty_webhook():
        """Break the response schema on purpose, skipping the server-side check."""
        answer = {"status": "accepted", "msg_id": "m-fault", "partition": "three"}
        log(f"fault route: sending an invalid response: {json.dumps(answer)}")
        return Response(json.dumps(answer), media_type="application/json")
