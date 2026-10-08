"""Store successful operation responses in the same transaction as their effects."""
import hashlib
import json
from decimal import Decimal
from exceptions.product_exceptions import BusinessConflict
from database.model import ApiOperation

def fingerprint(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True,
        default=lambda value: float(value) if isinstance(value, Decimal) else str(value),
        separators=(',', ':')).encode()).hexdigest()

def replay(session, key, payload):
    if not key:
        return None
    operation = session.get(ApiOperation, key)
    if operation is None:
        return None
    if operation.request_hash != fingerprint(payload):
        raise BusinessConflict('Idempotency key already used with different data')
    return json.loads(operation.response_json)

def remember(session, key, payload, response):
    if key:
        session.add(ApiOperation(key=key, request_hash=fingerprint(payload),
                                 response_json=json.dumps(response, default=str)))
        session.flush()
