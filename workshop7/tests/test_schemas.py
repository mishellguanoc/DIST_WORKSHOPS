import pytest

from common.validation import validate_request, validate_response

VALID_REQUEST = {
    "msg_id": "m-0001",
    "customer_id": "c-042",
    "session_id": "s-0007",
    "t_customer": "2026-11-05T10:15:30Z",
    "body": "Hello, is my order ready?",
    "delivery_attempt": 1,
}

ACCEPTED = {
    "status": "accepted",
    "msg_id": "m-0001",
    "partition": 3,
    "stream": "messages.p3",
    "sequence": 1,
}

REJECTED = {
    "status": "rejected",
    "errors": [{"path": "$.body", "message": "'body' is a required property"}],
}


def changed(document, **fields):
    return {**document, **fields}


def without(document, field):
    return {key: value for key, value in document.items() if key != field}


# Request


def test_valid_request():
    assert validate_request(VALID_REQUEST) == []


def test_request_with_optional_edge_case():
    assert validate_request(changed(VALID_REQUEST, edge_case="duplicate")) == []


@pytest.mark.parametrize("field", list(VALID_REQUEST))
def test_request_missing_required_field(field):
    errors = validate_request(without(VALID_REQUEST, field))
    assert len(errors) == 1
    assert field in errors[0]["message"]


@pytest.mark.parametrize(
    "field, value",
    [
        ("msg_id", 1),
        ("msg_id", ""),
        ("customer_id", None),
        ("session_id", ""),
        ("body", ""),
        ("body", "x" * 4097),
        ("delivery_attempt", "1"),
        ("delivery_attempt", 1.5),
        ("delivery_attempt", 0),
        ("edge_case", ""),
    ],
)
def test_request_invalid_value(field, value):
    errors = validate_request(changed(VALID_REQUEST, **{field: value}))
    assert [error["path"] for error in errors] == [f"$.{field}"]


@pytest.mark.parametrize(
    "value", ["yesterday", "2026-13-45T10:15:30Z", "2026-11-05", "2026-11-05 10:15:30"]
)
def test_request_invalid_date_time(value):
    errors = validate_request(changed(VALID_REQUEST, t_customer=value))
    assert [error["path"] for error in errors] == ["$.t_customer"]


def test_request_rejects_extra_field():
    errors = validate_request(changed(VALID_REQUEST, priority="high"))
    assert len(errors) == 1
    assert "priority" in errors[0]["message"]


def test_request_reports_every_error():
    document = changed(without(VALID_REQUEST, "body"), delivery_attempt=0)
    assert len(validate_request(document)) == 2


# Response


@pytest.mark.parametrize("document", [ACCEPTED, REJECTED])
def test_valid_response(document):
    assert validate_response(document) == []


@pytest.mark.parametrize(
    "document",
    [
        without(ACCEPTED, "sequence"),
        changed(ACCEPTED, partition=-1),
        changed(ACCEPTED, sequence=0),
        changed(ACCEPTED, status="queued"),
        changed(ACCEPTED, errors=REJECTED["errors"]),
        without(REJECTED, "errors"),
        changed(REJECTED, errors=[]),
        changed(REJECTED, errors=[{"path": "$.body"}]),
        changed(REJECTED, msg_id="m-0001"),
        {},
    ],
)
def test_invalid_response(document):
    assert validate_response(document) != []
