from fastapi import APIRouter
import database

router = APIRouter(prefix="/api/payments", tags=["payments"])

@router.post("/")
def registrar_pago(data: dict):
    order_id = data["order_id"]
    metodo = data["metodo"]
    monto = data["monto"]
    pago = database.Payment(database._next_payment_id, order_id, metodo, monto, True)
    database.payments[database._next_payment_id] = pago
    database._next_payment_id += 1
    return {"message": "Pago registrado", "pago": pago.__dict__}