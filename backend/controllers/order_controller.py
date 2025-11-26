from fastapi import APIRouter, HTTPException
import database

router = APIRouter(prefix="/api/orders", tags=["orders"])

@router.post("/")
def crear_pedido(data: dict):
    user_id = data.get("user_id") 
    # El frontend envía items como: [{productId: 1, quantity: 2}, ...]
    raw_items = data.get("items", [])
    payment_method = data.get("paymentMethod", "Efectivo")
    delivery_address = data.get("deliveryAddress", "")
    
    processed_items = []
    total_amount = 0
    
    # Buscamos los datos reales de cada producto en la BD
    for item in raw_items:
        dish = database.get_dish(item["productId"])
        if dish:
            # Guardamos el nombre y precio ACTUAL en el pedido
            item_total = dish["precio"] * item["quantity"]
            total_amount += item_total
            
            processed_items.append({
                "id": dish["id"],
                "name": dish["nombre"],
                "price": dish["precio"],
                "quantity": item["quantity"]
            })
            
    if not processed_items:
        raise HTTPException(status_code=400, detail="No hay productos válidos en el pedido")

    # Guardamos el pedido completo en MongoDB
    pedido = database.create_order(
        user_id=user_id,
        items=processed_items, # Lista detallada
        total=total_amount,
        estado="pendiente",
        payment_method=payment_method,
        delivery_address=delivery_address
    )
    
    # Devolvemos el ID para que el frontend redirija a la boleta
    return {"message": "Pedido creado", "orderId": pedido["id"], "pedido": pedido}

@router.get("/{order_id}")
def obtener_pedido(order_id: int):
    order = database.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # Enriquecer datos del cliente para la boleta
    client_name = "Cliente Invitado"
    client_email = "N/A"
    
    if order.get("user_id"):
        user = database.users_collection.find_one({"id": order["user_id"]})
        if user:
            client_name = user["nombre"]
            client_email = user["email"]
            
    # Estructura lista para la Boleta
    return {
        "id": order["id"],
        "createdAt": str(order.get("_id").generation_time), # Fecha real de Mongo
        "totalAmount": order["total"],
        "status": order["estado"],
        "clientName": client_name,
        "clientEmail": client_email,
        "deliveryAddress": order.get("delivery_address", "Retiro en tienda"),
        "paymentMethod": order.get("payment_method", "Efectivo"),
        "items": [
            {
                "productName": item["name"],
                "quantity": item["quantity"],
                "priceAtPurchase": item["price"]
            } for item in order["items"]
        ],
        "repartidorNombre": order.get("repartidorNombre")
    }
    
# Endpoint para listar (para Cocina y Delivery)
@router.get("/")
def listar_pedidos():
    return database.get_all_orders()

# Endpoint para cambiar estado (Cocina / Delivery / Anular)
@router.patch("/{order_id}/status")
def update_status(order_id: int, data: dict):
    new_status = data.get("status")
    database.update_order_status(order_id, new_status)
    return {"message": "Estado actualizado"}

@router.patch("/{order_id}/assign")
def assign_driver(order_id: int, data: dict):
    driver_name = data.get("repartidorNombre")
    database.assign_order(order_id, driver_name)
    return {"message": "Repartidor asignado"}