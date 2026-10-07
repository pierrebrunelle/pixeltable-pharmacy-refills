"""Pharmacy Refill API built with Pixeltable.

    export REFILL_SIGNING_KEY=<any-long-random-string>
    pxt schema update app.py pharmacy
    pxt service run app.py pharmacy
"""
from pixeltable.serving import FastAPIRouter

from models import Prescriptions, Refills, TableModel  # noqa: F401  (TableModel lets `pxt schema` find the models)
from queries import patient_prescriptions, queue

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
