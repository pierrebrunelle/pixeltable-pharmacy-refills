"""Sign, request, advance and query refills through the API (the service needs REFILL_SIGNING_KEY).

Usage:
    python client_demo.py                             # local service on port 8000
    python client_demo.py https://<your-service-url>  # hosted service; set PIXELTABLE_API_KEY first

Standard library only. If PIXELTABLE_API_KEY is set it is sent as the X-api-key header.
Exits non-zero if any call returns an unexpected status code.
"""
import concurrent.futures as cf
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

BASE = (sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8000').rstrip('/')
API_KEY = os.environ.get('PIXELTABLE_API_KEY')
HERE = Path(__file__).resolve().parent
FAILURES: list[str] = []


def _send(req: urllib.request.Request) -> tuple[int, object]:
    if API_KEY:
        req.add_header('X-api-key', API_KEY)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            if 'json' in (resp.headers.get('Content-Type') or ''):
                return resp.status, json.loads(raw or b'null')
            return resp.status, f'<{len(raw)} bytes {resp.headers.get("Content-Type")}>'
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')[:300]


def call(method: str, path: str, body: dict | None = None) -> tuple[int, object]:
    data = json.dumps(body).encode() if body is not None else None
    return _send(urllib.request.Request(BASE + path, data=data, method=method,
                                        headers={'Content-Type': 'application/json'}))


def upload(path: str, fields: dict, files: dict) -> tuple[int, object]:
    """multipart/form-data POST: fields are form values, files maps field name -> local file path."""
    boundary = uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    for k, fp in files.items():
        fp = Path(fp)
        ctype = mimetypes.guess_type(fp.name)[0] or 'application/octet-stream'
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"; filename="{fp.name}"\r\n'
                     f'Content-Type: {ctype}\r\n\r\n'.encode() + fp.read_bytes() + b'\r\n')
    body = b''.join(parts) + f'--{boundary}--\r\n'.encode()
    return _send(urllib.request.Request(BASE + path, data=body, method='POST',
                                        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}))


def check(label: str, code: int, out: object, expect: int = 200):
    print(f'{label:<36} {code}  {json.dumps(out)[:180]}')
    if code != expect:
        FAILURES.append(f'{label}: got {code}, expected {expect}')
    return out


def show(label: str, method: str, path: str, body: dict | None = None, expect: int = 200):
    code, out = call(method, path, body)
    return check(label, code, out, expect)


def parallel(label: str, n: int, fn) -> list:
    with cf.ThreadPoolExecutor(max_workers=min(n, 16)) as pool:
        results = list(pool.map(fn, range(n)))
    codes = sorted({c for c, _ in results})
    print(f'{label:<36} {n} calls, status codes: {codes}')
    if codes != [200]:
        FAILURES.append(f'{label}: status codes {codes}')
    return results


def q(s: str) -> str:
    return urllib.parse.quote(s)


show('sign a receipt (compute)', 'POST', '/sign', {'rx_number': 'RX-100245', 'requested_at': '2026-10-06T09:00', 'status': 'requested'})
show('new prescription', 'POST', '/prescriptions', {'rx_number': 'RX-100310', 'patient_ref': 'P-21c9', 'drug': 'metformin 500 mg',
                                                    'refills_left': 5, 'prescriber': 'Dr. Mbeki'})
r = show('request a refill', 'POST', '/refills', {'rx_number': 'RX-100245', 'patient_ref': 'P-7f3a',
                                                  'requested_at': '2026-10-06T09:00', 'channel': 'drive-thru', 'status': 'requested'})
rid = r.get('id') if isinstance(r, dict) else None
r2 = show('mark it ready (receipt re-signed)', 'POST', '/refills/status', {'id': rid, 'status': 'ready'})
if isinstance(r, dict) and isinstance(r2, dict) and r.get('receipt_sig') == r2.get('receipt_sig'):
    FAILURES.append('receipt was not re-signed after the status change')
show('requested queue', 'GET', '/refills/queue?status=requested')
show('ready queue', 'GET', '/refills/queue?status=ready')
show("P-7f3a's prescriptions", 'GET', '/patients/prescriptions?patient_ref=P-7f3a')


if FAILURES:
    print('\nFAILED:', *FAILURES, sep='\n  ')
    sys.exit(1)
print('\nall calls OK')
