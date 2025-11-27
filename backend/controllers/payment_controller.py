from fastapi import APIRouter, HTTPException
import database

router = APIRouter(prefix="/api/payments", tags=["payments"])

@router.post("/")
def registrar_pago(data: dict):
    order_id = data.get("order_id")
    
    # 1. Verificar que la orden exista
    order = database.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada para el pago")

    # 2. Guardar el pago
    payment_doc = {
        "order_id": order_id,
        "metodo": data.get("metodo"),
        "monto": data.get("monto"),
        "confirmado": True
    }
    database.payments_collection.insert_one(payment_doc)
    payment_doc.pop("_id")
    
    # 3. --- NUEVO: Generar Boleta (SalesReceipt) ---
    # Obtenemos info del cliente
    user = database.users_collection.find_one({"id": order["user_id"]})
    client_data = {
        "nombre": user["nombre"] if user else "Cliente Invitado",
        "email": user["email"] if user else "N/A",
        "address": order.get("delivery_address", "Retiro en Tienda")
    }
    
    database.create_receipt(
        order_id=order_id,
        client_data=client_data,
        items=order["items"],
        total=order["total"],
        payment_method=data.get("metodo")
    )
    
    return {"message": "Pago registrado y boleta generada", "pago": payment_doc}