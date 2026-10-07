"""Seed synthetic prescriptions and refill requests (needs REFILL_SIGNING_KEY in the environment).

Usage:
    python seed.py            # seeds the local `pharmacy` catalog directory
    python seed.py my_dir     # or another directory you passed to `pxt schema update`
"""
import sys
from pathlib import Path

import pixeltable as pxt

target = sys.argv[1] if len(sys.argv) > 1 else 'pharmacy'
HERE = Path(__file__).resolve().parent

SEED = {
    'prescriptions': [
        {'rx_number': 'RX-100231', 'patient_ref': 'P-7f3a', 'drug': 'atorvastatin 20 mg', 'refills_left': 3, 'prescriber': 'Dr. Lindqvist'},
        {'rx_number': 'RX-100245', 'patient_ref': 'P-7f3a', 'drug': 'lisinopril 10 mg', 'refills_left': 1, 'prescriber': 'Dr. Lindqvist'},
        {'rx_number': 'RX-100298', 'patient_ref': 'P-21c9', 'drug': 'levothyroxine 50 mcg', 'refills_left': 0, 'prescriber': 'Dr. Mbeki'},
    ],
    'refills': [
        {'rx_number': 'RX-100231', 'patient_ref': 'P-7f3a', 'requested_at': '2026-10-06T08:15', 'channel': 'app', 'status': 'requested'},
        {'rx_number': 'RX-100298', 'patient_ref': 'P-21c9', 'requested_at': '2026-10-06T08:40', 'channel': 'counter', 'status': 'ready'},
    ],
}

for table_name, rows in SEED.items():
    t = pxt.get_table(f'{target}/{table_name}')
    if t.count() > 0:
        print(f'{target}/{table_name} already has {t.count()} rows; skipping')
        continue
    for row in rows:
        for k, v in row.items():
            if isinstance(v, str) and v.startswith('data/'):
                row[k] = str(HERE / v)   # local sample media file
    t.insert(rows)
    print(f'inserted {len(rows)} rows into {target}/{table_name}')
