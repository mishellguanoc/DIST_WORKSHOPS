"""JSON Schema validation shared by the client and the server."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"


def _load_validator(filename):
    schema = json.loads((SCHEMA_DIR / filename).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    # Without a FormatChecker, "format": "date-time" is only an annotation.
    return Draft202012Validator(schema, format_checker=FormatChecker())


REQUEST_VALIDATOR = _load_validator("webhook_request.schema.json")
RESPONSE_VALIDATOR = _load_validator("webhook_response.schema.json")


def _collect_errors(validator, document):
    errors = sorted(validator.iter_errors(document), key=lambda e: e.json_path)
    return [{"path": e.json_path, "message": e.message} for e in errors]


def validate_request(document):
    """Return a list of {path, message}; it is empty when the document is valid."""
    return _collect_errors(REQUEST_VALIDATOR, document)


def validate_response(document):
    """Return a list of {path, message}; it is empty when the document is valid."""
    return _collect_errors(RESPONSE_VALIDATOR, document)
