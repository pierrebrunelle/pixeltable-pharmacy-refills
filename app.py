"""Pharmacy Refill API built with Pixeltable.

    export REFILL_SIGNING_KEY=<any-long-random-string>
    pxt schema update app.py pharmacy
    pxt service run app.py pharmacy
"""
import pixeltable as pxt
import pixeltable.functions as pxtf
from pixeltable.serving import FastAPIRouter

from udfs import receipt_signature, refill_state, status_label

# ---- tables ----
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


# ---- queries ----
@pxt.query
def queue(status: str):
    """Refills in one status, oldest request first (status index)."""
    return Refills.where(Refills.status == status).select(
        Refills.id, Refills.rx_number, Refills.requested_at, Refills.label
    ).order_by(Refills.requested_at)


@pxt.query
def patient_prescriptions(patient_ref: str):
    """A patient's prescriptions (patient_ref index)."""
    return Prescriptions.where(Prescriptions.patient_ref == patient_ref).select(
        Prescriptions.rx_number, Prescriptions.drug, Prescriptions.refills_left, Prescriptions.state
    ).order_by(Prescriptions.rx_number)


# ---- routes ----
refill_api = FastAPIRouter(name='refill_api')
refill_api.add_insert_route(
    Prescriptions, path='/prescriptions',
    inputs=[Prescriptions.rx_number, Prescriptions.patient_ref, Prescriptions.drug, Prescriptions.refills_left,
            Prescriptions.prescriber],
    outputs=[Prescriptions.rx_number, Prescriptions.state],
)
refill_api.add_insert_route(
    Refills, path='/refills',
    inputs=[Refills.rx_number, Refills.patient_ref, Refills.requested_at, Refills.channel, Refills.status],
    outputs=[Refills.id, Refills.label, Refills.receipt_sig],
)
refill_api.add_update_route(Refills, path='/refills/status', inputs=[Refills.status],
                            outputs=[Refills.id, Refills.label, Refills.receipt_sig])
refill_api.add_compute_route(Refills, path='/sign',
                             inputs=[Refills.rx_number, Refills.requested_at, Refills.status],
                             outputs=[Refills.receipt_sig])
refill_api.add_query_route(path='/refills/queue', query=queue, method='get')
refill_api.add_query_route(path='/patients/prescriptions', query=patient_prescriptions, method='get')
