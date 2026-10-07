"""Refill queue queries."""
import pixeltable as pxt

from models import Prescriptions, Refills


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
