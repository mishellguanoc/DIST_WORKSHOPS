# Workshop 7: data interchange using JSON

Two components exchange JSON between two machines, with and without a predefined schema.

| Machine | Runs |
|---|---|
| A: Windows 11 | Clients, demos and benchmark |
| B: WSL2 Ubuntu | FastAPI services |

| Service | Port | Schema |
|---|---|---|
| `ingestion`: `POST /webhook` | 8000 | JSON Schema on the request and response, validated on both sides |
| `ingestion`: `POST /control/webhook` | 8000 | Same work without validation, used as the benchmark control |
| `wa_mock`: `POST /messages` | 8001 | None |

## Setup

Windows, from `workshop7`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

WSL, from `workshop7`, with [uv](https://docs.astral.sh/uv/) installed:

```bash
uv venv --python 3.12 ~/w7-venv
uv pip install --python ~/w7-venv/bin/python -r requirements.txt
```

Get the address of the WSL machine with `hostname -I`, and use it as `<WSL_IP>` below. It can change after a restart.

## Run

Schema tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -v
```

Activity 1, with the service in WSL and the client on Windows. `W7_FAULTS=1` enables the route that `demo_validation.py` needs:

```bash
W7_FAULTS=1 ~/w7-venv/bin/python -m uvicorn services.ingestion_service:app --host 0.0.0.0 --port 8000
```

```powershell
.\.venv\Scripts\python.exe -m clients.webhook_client --host <WSL_IP>
.\.venv\Scripts\python.exe demo_validation.py --host <WSL_IP>
```

Activity 2:

```bash
~/w7-venv/bin/python -m uvicorn services.wa_mock_service:app --host 0.0.0.0 --port 8001
```

```powershell
.\.venv\Scripts\python.exe -m clients.messages_client --host <WSL_IP>
.\.venv\Scripts\python.exe demo_schemaless.py --host <WSL_IP>
```

Benchmark. Stop the services above first, because the script uses the same ports:

```bash
bash scripts/start_wsl_services.sh
```

```powershell
.\.venv\Scripts\python.exe -m benchmark.run_benchmark --host <WSL_IP>
.\.venv\Scripts\python.exe -m benchmark.analyze
```

Results are saved in `results/`: `raw_*.csv`, `meta.json`, `summary.json` and the figure.

## Layout

- `schemas/`: JSON Schemas for the webhook request and response
- `common/`: validation, timing and payload generation
- `services/`, `clients/`: the two services and their clients
- `benchmark/`: measurement and analysis
- `report/report.tex`: the report, using the IEEEtran class
