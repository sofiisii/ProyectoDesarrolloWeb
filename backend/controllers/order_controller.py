from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from datetime import datetime
import random
import database

router = APIRouter(prefix="/api/orders", tags=["orders"])

REPARTIDORES_DISPONIBLES = [
    "Juan Pérez", "María González", "Carlos López", 
    "Ana Martínez", "Pedro Sánchez", "Luisa Fernández"
]

# --- LÓGICA DE SIMULACIÓN AUTOMÁTICA ---
def simulate_order_progression(order):
    if order.get("estado") == "anulado":
        return order

    created_at = order.get("created_at")
    if not created_at:
        return order

    now = datetime.now()
    elapsed_seconds = (now - created_at).total_seconds()

    estado_actual = order["estado"]
    nuevo_estado = estado_actual
    
    # Cronograma de simulación
    if elapsed_seconds < 20:       
        nuevo_estado = "pendiente"
    elif elapsed_seconds < 60:     
        nuevo_estado = "preparando"
    elif elapsed_seconds < 90:     
        nuevo_estado = "completado"
    elif elapsed_seconds < 120:    
        nuevo_estado = "en_ruta"
    else:                          
        nuevo_estado = "entregado"

    # Actualizar solo si cambia y NO fue anulado manualmente antes
    if nuevo_estado != estado_actual and estado_actual != "anulado":
        
        # Asignar chofer al pasar a en_ruta
        if nuevo_estado == "en_ruta" and not order.get("repartidorNombre"):
            chofer = random.choice(REPARTIDORES_DISPONIBLES)
            database.assign_order(order["id"], chofer)
            order["repartidorNombre"] = chofer
        
        database.update_order_status(order["id"], nuevo_estado)
        order["estado"] = nuevo_estado

    return order

def format_order_response(order):
    order = simulate_order_progression(order) # Aplicar simulación

    client_name = "Cliente Invitado"
    client_email = "N/A"
    
    if order.get("user_id"):
        user = database.users_collection.find_one({"id": order["user_id"]})
        if user:
            client_name = user.get("nombre", "Sin nombre")
            client_email = user.get("email", "Sin email")
            
    fecha_creacion = order.get("created_at")
    fecha_str = str(fecha_creacion) if fecha_creacion else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "id": order["id"],
        "createdAt": fecha_str,
        "totalAmount": order.get("total", 0),
        "status": order.get("estado", "pendiente"),
        "clientName": client_name,
        "clientEmail": client_email,
        "deliveryAddress": order.get("delivery_address", "Retiro en tienda"),
        "paymentMethod": order.get("payment_method", "Efectivo"),
        "items": order.get("items", []),
        "repartidorNombre": order.get("repartidorNombre")
    }

# --- ENDPOINTS ---

@router.post("/")
def crear_pedido(data: dict, Authorization: Optional[str] = Header(default=None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Debes iniciar sesión")
    
    token = Authorization.split(" ")[1]
    user = database.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=403, detail="Sesión inválida")
        
    processed_items = []
    total_amount = 0
    for item in data.get("items", []):
        dish = database.get_dish(item["productId"])
        if dish:
            total_amount += dish["precio"] * item["quantity"]
            processed_items.append({
                "productName": dish["nombre"], # Guardamos nombre directo
                "quantity": item["quantity"],
                "priceAtPurchase": dish["precio"]
            })
    
    pedido = database.create_order(
        user_id=user["id"], 
        items=processed_items, 
        total=total_amount, 
        estado="pendiente", 
        payment_method=data.get("paymentMethod", "Efectivo"), 
        delivery_address=data.get("deliveryAddress", "")
    )
    return {"message": "Pedido creado", "orderId": pedido["id"], "pedido": format_order_response(pedido)}

@router.get("/current")
def get_current_order(Authorization: Optional[str] = Header(default=None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
    
    token = Authorization.split(" ")[1]
    user = database.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=403, detail="Sesión expirada")
        
    order = database.get_latest_order_by_user(user["id"])
    if not order:
        raise HTTPException(status_code=404, detail="No tienes pedidos activos")
        
    return format_order_response(order)

@router.get("/history")
def get_order_history(Authorization: Optional[str] = Header(default=None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
    token = Authorization.split(" ")[1]
    user = database.get_user_by_token(token)
    orders = database.get_orders_by_user(user["id"])
    return [format_order_response(o) for o in orders]

@router.get("/{order_id}")
def obtener_pedido(order_id: int):
    order = database.get_order_by_id(order_id)
    if not order: raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return format_order_response(order)

# --- NUEVO ENDPOINT DE ANULACIÓN (REGLAS DE NEGOCIO PDF) ---
@router.post("/{order_id}/cancel")
def cancel_order(order_id: int, Authorization: Optional[str] = Header(default=None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
    
    # 1. Obtener pedido real
    order = database.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    # 2. Verificar estado (Regla de Negocio)
    # Si ya está en ruta o entregado, NO se puede anular
    if order["estado"] in ["en_ruta", "entregado"]:
        raise HTTPException(status_code=400, detail="No es posible anular con el pedido en ruta o entregado")
    
    if order["estado"] == "anulado":
        return {"message": "El pedido ya estaba anulado"}

    # 3. Proceder con anulación
    database.update_order_status(order_id, "anulado")
    return {"message": "Pedido anulado exitosamente. La venta ha sido revertida."}

@router.patch("/{order_id}/status")
def update_status(order_id: int, data: dict):
    database.update_order_status(order_id, data.get("status"))
    return {"message": "Estado actualizado"}

@router.patch("/{order_id}/assign")
def assign_driver(order_id: int, data: dict):
    database.assign_order(order_id, data.get("repartidorNombre"))
    return {"message": "Repartidor asignado"}