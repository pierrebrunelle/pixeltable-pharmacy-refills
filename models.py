"""Prescriptions and refill requests, with B-tree indexes and a signed computed column."""
import pixeltable as pxt
import pixeltable.functions as pxtf

from udfs import receipt_signature, refill_state, status_label

TableModel = pxt.model_base()


class Prescriptions(TableModel, name='prescriptions', has_default_idxs=False):
    rx_number = pxt.Column(type=pxt.String, primary_key=True)
    patient_ref: pxt.String          # an opaque reference, not a name
    drug: pxt.String
    refills_left: pxt.Int
    prescriber: pxt.String

    state = refill_state(refills_left)

    __indexes__ = [pxt.BtreeIndex(patient_ref), pxt.BtreeIndex(drug)]


class Refills(TableModel, name='refills', has_default_idxs=False):
    id = pxt.Column(value=pxtf.uuid.uuid7(), primary_key=True)
    rx_number: pxt.String
    patient_ref: pxt.String
    requested_at: pxt.String
    channel: pxt.String              # counter / app / drive-thru
    status: pxt.String               # requested / ready / picked-up

    label = status_label(status, channel)
    receipt_sig = receipt_signature(rx_number, requested_at, status)   # re-signed when status changes

    __indexes__ = [pxt.BtreeIndex(rx_number), pxt.BtreeIndex(status)]
