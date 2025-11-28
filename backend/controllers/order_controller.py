from fastapi import APIRouter, HTTPException, Header
from typing import Optional
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

# --- FUNCIÓN AUXILIAR PARA FORMATEAR PEDIDOS ---
def format_order_response(order):
    client_name = "Cliente Invitado"
    client_email = "N/A"
    if order.get("user_id"):
        user = database.users_collection.find_one({"id": order["user_id"]})
        if user:
            client_name = user["nombre"]
            client_email = user["email"]
            
    return {
        "id": order["id"],
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

# --- NUEVO ENDPOINT: Obtener el pedido actual del usuario logueado ---
@router.get("/current")
def get_current_order(Authorization: Optional[str] = Header(default=None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
    
    token = Authorization.split(" ")[1]
    user = database.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=403, detail="Sesión expirada")
        
    # Buscar el último pedido de este usuario
    order = database.get_latest_order_by_user(user["id"])
    if not order:
        raise HTTPException(status_code=404, detail="No tienes pedidos activos")
        
    return format_order_response(order)

@router.get("/{order_id}")
def obtener_pedido(order_id: int):
    order = database.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return format_order_response(order)
    
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