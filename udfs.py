"""Pixeltable UDFs for the refill queue (recorded by module path, e.g. `udfs.receipt_signature`).

receipt_signature reads REFILL_SIGNING_KEY from the environment when it runs; the key is never stored.
"""
import hashlib
import hmac
import os

import pixeltable as pxt


@pxt.udf
def receipt_signature(rx_number: str, requested_at: str, status: str) -> str:
    """HMAC-SHA256 over 'rx|requested_at|status', keyed by REFILL_SIGNING_KEY."""
    key = os.environ.get('REFILL_SIGNING_KEY')
    if not key:
        raise RuntimeError('REFILL_SIGNING_KEY is not set')
    msg = f'{rx_number}|{requested_at}|{status}'.encode()
    return hmac.new(key.encode(), msg, hashlib.sha256).hexdigest()[:32]


@pxt.udf
def refill_state(refills_left: int) -> str:
    return 'renewal-needed' if refills_left <= 0 else ('last-refill' if refills_left == 1 else 'ok')


@pxt.udf
def status_label(status: str, channel: str) -> str:
    """'ready (drive-thru)' etc."""
    return f'{status} ({channel})'
