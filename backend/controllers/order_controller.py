from fastapi import APIRouter, HTTPException
import database

router = APIRouter(prefix="/api/orders", tags=["orders"])

@router.post("/")
def crear_pedido(data: dict):
    user_id = data.get("user_id")
    raw_items = data.get("items", [])
    payment_method = data.get("paymentMethod", "Efectivo")
    delivery_address = data.get("deliveryAddress", "")
    
    processed_items = []
    total_amount = 0
    
    for item in raw_items:
        dish = database.get_dish(item["productId"])
        if dish:
            item_total = dish["precio"] * item["quantity"]
            total_amount += item_total
            processed_items.append({
                "id": dish["id"],
                "name": dish["nombre"],
                "price": dish["precio"],
                "quantity": item["quantity"]
            })
            
    if not processed_items:
        raise HTTPException(status_code=400, detail="No hay productos válidos")

    pedido = database.create_order(user_id, processed_items, total_amount, "pendiente", payment_method, delivery_address)
    return {"message": "Pedido creado", "orderId": pedido["id"], "pedido": pedido}

@router.get("/{order_id}")
def obtener_pedido(order_id: int):
    # 1. Buscar la orden
    order = database.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # 2. --- NUEVO: Intentar buscar la Boleta Oficial ---
    receipt = database.get_receipt_by_order_id(order_id)
    
    if receipt:
        # Si ya existe la boleta (se pagó), devolvemos los datos congelados de la boleta
        return {
            "id": receipt["id"], # ID de la boleta (ej. 1, 2...)
            "orderId": order["id"],
            "createdAt": str(receipt["date"]),
            "totalAmount": receipt["total"],
            "status": order["estado"], # El estado sigue viniendo de la orden
            "clientName": receipt["clientName"],
            "clientEmail": receipt["clientEmail"],
            "deliveryAddress": receipt["clientAddress"],
            "paymentMethod": receipt["paymentMethod"],
            "items": [
                {
                    "productName": item["name"],
                    "quantity": item["quantity"],
                    "priceAtPurchase": item["price"]
                } for item in receipt["products"]
            ]
        }
    
    # 3. Si NO hay boleta aún (no pagado), mostramos datos preliminares de la orden
    client_name = "Cliente Invitado"
    client_email = "N/A"
    if order.get("user_id"):
        user = database.users_collection.find_one({"id": order["user_id"]})
        if user:
            client_name = user["nombre"]
            client_email = user["email"]
            
    return {
        "id": order["id"], # ID provisional (de la orden)
        "createdAt": str(order.get("created_at", "Reciente")),
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
    
@router.get("/")
def listar_pedidos():
    return database.get_all_orders()

@router.patch("/{order_id}/status")
def update_status(order_id: int, data: dict):
    database.update_order_status(order_id, data.get("status"))
    return {"message": "Estado actualizado"}

@router.patch("/{order_id}/assign")
def assign_driver(order_id: int, data: dict):
    database.assign_order(order_id, data.get("repartidorNombre"))
    return {"message": "Repartidor asignado"}