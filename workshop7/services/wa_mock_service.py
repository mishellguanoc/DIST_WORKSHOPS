"""Activity 2: WhatsApp API mock with no predefined schema (machine B, WSL).

Fields are read with .get() and never checked, so wrong data is not detected.
"""

import itertools
import json
import os
import platform
from datetime import timedelta

from fastapi import FastAPI, Request, Response

from common.payloads import SIMULATED_NOW, customer_last_seen
from common.timing import StageTimer

WINDOW = timedelta(hours=24)
MACHINE = platform.system()
QUIET = os.environ.get("W7_QUIET") == "1"

app = FastAPI(title="wa_mock")

last_seen = customer_last_seen()
message_ids = itertools.count(1)


def log(text):
    if not QUIET:
        print(f"[wa_mock@{MACHINE}] {text}", flush=True)


def window_is_open(customer_id):
    last_message = last_seen.get(customer_id)
    return last_message is not None and SIMULATED_NOW <= last_message + WINDOW


def json_response(document, status_code, timer):
    body = json.dumps(document, separators=(",", ":")).encode("utf-8")
    timer.lap("serialize")
    return Response(
        body,
        status_code,
        media_type="application/json",
        headers={"Server-Timing": timer.server_timing()},
    )


@app.post("/messages")
async def messages(request: Request):
    raw = await request.body()
    timer = StageTimer()

    try:
        message = json.loads(raw)
    except ValueError as error:
        timer.lap("parse")
        return json_response({"error": {"message": f"invalid JSON: {error}"}}, 400, timer)
    timer.lap("parse")

    customer_id = message.get("customer_id")
    if window_is_open(customer_id):
        answer = {"status": "sent", "message_id": f"wamid.{next(message_ids):06d}"}
        status_code, error_code = 200, None
    else:
        answer = {"error": {"code": 131047, "message": "Re-engagement message"}}
        status_code, error_code = 400, 131047
    timer.lap("handle")

    response = json_response(answer, status_code, timer)

    # Logged last so that printing is not counted in the stage timings.
    record = {
        "customer_id": customer_id,
        "kind": message.get("kind"),
        "in_reply_to": message.get("in_reply_to"),
        "body": message.get("body"),
        "fencing_meta": message.get("fencing_meta"),
        "http_status": status_code,
        "error_code": error_code,
    }
    log(f"received from {request.client.host}: {raw.decode('utf-8', 'replace')}")
    log(f"attempt logged: {json.dumps(record)}")
    return response


@app.get("/info")
async def info(request: Request):
    return {
        "system": platform.system(),
        "release": platform.release(),
        "python": platform.python_version(),
        "client_seen_as": request.client.host,
    }
