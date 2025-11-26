from fastapi import APIRouter
import database

router = APIRouter(prefix="/api/payments", tags=["payments"])

@router.post("/")
def registrar_pago(data: dict):
    # Usamos la colección de pagos de MongoDB
    # Nota: En un caso real, aquí integrarías Stripe/PayPal.
    # Por ahora solo guardamos el registro en la BD.
    
    payment_doc = {
        "order_id": data.get("order_id"),
        "metodo": data.get("metodo"),
        "monto": data.get("monto"),
        "confirmado": True
    }
    
    # Insertar en MongoDB
    database.payments_collection.insert_one(payment_doc)
    
    # Convertir a string el _id para devolverlo (o quitarlo)
    payment_doc.pop("_id")
    
    return {"message": "Pago registrado", "pago": payment_doc}