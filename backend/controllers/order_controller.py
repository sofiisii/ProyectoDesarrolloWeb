from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from datetime import datetime
import random
import database

router = APIRouter(prefix="/api/orders", tags=["orders"])

REPARTIDORES_DISPONIBLES = ["Juan Pérez", "María González", "Carlos López", "Ana Martínez"]

# --- LÓGICA HÍBRIDA: SIMULACIÓN SOLO PARA DELIVERY ---
def simulate_delivery_progression(order):
    """
    Solo avanza el pedido si ya salió de cocina (estado 'completado' o superior).
    """
    estado_actual = order.get("estado")
    
    # Si está anulado, pendiente o preparando, NO HACEMOS NADA (Manual)
    if estado_actual in ["anulado", "pendiente", "preparando"]:
        return order

    # Si ya está entregado, tampoco hacemos nada
    if estado_actual == "entregado":
        return order

    # --- AQUI EMPIEZA LA SIMULACIÓN DE DELIVERY ---
    # La referencia de tiempo será la última actualización ('updated_at')
    # Si no existe, usamos 'created_at' (aunque idealmente deberíamos guardar cuándo se completó)
    
    # Para simplificar la demo, usaremos el tiempo transcurrido desde que se creó,
    # pero asumiendo que la cocina ya terminó.
    
    created_at = order.get("created_at")
    if not created_at: return order
    
    now = datetime.now()
    elapsed_seconds = (now - created_at).total_seconds()
    
    nuevo_estado = estado_actual

    # Lógica de tiempos para la demo:
    # Supongamos que el cocinero se demora unos segundos/minutos en marcar "Listo".
    # Una vez que está "completado", el sistema de delivery espera un poco y lo pasa a "en_ruta".
    
    # Ajustamos umbrales para que se sienta natural en la demo:
    # Si ya es "completado", pasará a "en_ruta" si el pedido tiene más de X tiempo total
    # Ojo: Esto depende de qué tan rápido seas en la cocina.
    
    # ESTRATEGIA MEJORADA: Usar probabilidad o tiempo forzado desde que está completado.
    # Como no guardamos "completed_at", usaremos una regla simple:
    # Si está "completado", tiene un 10% de chance de pasar a "en_ruta" cada vez que se consulta (aprox cada 3-5 seg)
    # Esto simula que el repartidor llega a recogerlo.
    
    # SIN EMBARGO, para ser predecible en la demo, usaremos el tiempo total:
    
    if estado_actual == "completado":
        # Si han pasado más de 60 segundos desde la creación Y está listo, sale a ruta
        if elapsed_seconds > 60: 
            nuevo_estado = "en_ruta"
            
    elif estado_actual == "en_ruta":
        # Si lleva más de 120 segundos total (2 min), se entrega
        if elapsed_seconds > 120:
            nuevo_estado = "entregado"

    # Actualizar si hubo cambio
    if nuevo_estado != estado_actual:
        # Asignar chofer si pasa a ruta
        if nuevo_estado == "en_ruta" and not order.get("repartidorNombre"):
            chofer = random.choice(REPARTIDORES_DISPONIBLES)
            database.assign_order(order["id"], chofer)
            order["repartidorNombre"] = chofer
            print(f"--> DELIVERY: Chofer {chofer} asignado al pedido #{order['id']}")
        
        database.update_order_status(order["id"], nuevo_estado)
        order["estado"] = nuevo_estado
        print(f"--> DELIVERY: Pedido #{order['id']} avanzó a {nuevo_estado}")

    return order

def format_order_response(order):
    # Aplicamos la simulación HÍBRIDA
    order = simulate_delivery_progression(order)
    
    client_name = "Invitado"
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
        "originalAmount": order.get("original_total", order.get("total", 0)),
        "discount": order.get("discount", 0),
        "promoName": order.get("promo_name", ""),
        "status": order.get("estado", "pendiente"),
        "clientName": client_name,
        "clientEmail": client_email,
        "deliveryAddress": order.get("delivery_address", "Retiro en tienda"),
        "paymentMethod": order.get("payment_method", "Efectivo"),
        "items": order.get("items", []),
        "repartidorNombre": order.get("repartidorNombre")
    }

# --- ENDPOINTS (Sin cambios mayores) ---

@router.get("/")
def listar_pedidos():
    pedidos = database.get_all_orders()
    # También aplicamos la simulación al listar para que el admin vea los cambios
    return [format_order_response(p) for p in pedidos]

@router.post("/")
def crear_pedido(data: dict, Authorization: Optional[str] = Header(default=None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Debes iniciar sesión")
    
    token = Authorization.split(" ")[1]
    user = database.get_user_by_token(token)
    if not user: raise HTTPException(status_code=403, detail="Sesión inválida")
    
    processed_items = []
    subtotal = 0
    for item in data.get("items", []):
        dish = database.get_dish(item["productId"])
        if dish:
            item_total = dish["precio"] * item["quantity"]
            subtotal += item_total
            processed_items.append({
                "productName": dish["nombre"],
                "quantity": item["quantity"],
                "priceAtPurchase": dish["precio"]
            })
            
    if not processed_items:
        raise HTTPException(status_code=400, detail="Carrito vacío")

    categoria = user.get("categoria", "nuevo")
    discount = 0
    promo_name = ""
    if categoria == "frecuente":
        discount = subtotal * 0.10
        promo_name = "Descuento Cliente Frecuente"
    elif categoria == "vip":
        discount = subtotal * 0.20
        promo_name = "Descuento VIP"
    
    pedido = database.create_order(
        user_id=user["id"], 
        items=processed_items, 
        total=subtotal - discount, 
        estado="pendiente", # Empieza manual
        payment_method=data.get("paymentMethod", "Efectivo"), 
        delivery_address=data.get("deliveryAddress", ""),
        discount=discount,
        promo_name=promo_name
    )
    return {"message": "Pedido creado", "orderId": pedido["id"], "pedido": format_order_response(pedido)}

@router.get("/current")
def get_current_order(Authorization: Optional[str] = Header(default=None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
    token = Authorization.split(" ")[1]
    user = database.get_user_by_token(token)
    if not user: raise HTTPException(status_code=403, detail="Sesión expirada")
    
    order = database.get_latest_order_by_user(user["id"])
    if not order: raise HTTPException(status_code=404, detail="No tienes pedidos activos")
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

@router.post("/{order_id}/cancel")
def cancel_order(order_id: int, Authorization: Optional[str] = Header(default=None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
    order = database.get_order_by_id(order_id)
    if not order: raise HTTPException(status_code=404, detail="Pedido no encontrado")
    
    if order["estado"] in ["en_ruta", "entregado"]:
        raise HTTPException(status_code=400, detail="No es posible anular con el pedido en ruta o entregado")
    
    database.update_order_status(order_id, "anulado")
    return {"message": "Pedido anulado correctamente"}

@router.patch("/{order_id}/status")
def update_status(order_id: int, data: dict):
    database.update_order_status(order_id, data.get("status"))
    return {"message": "Estado actualizado"}

@router.patch("/{order_id}/assign")
def assign_driver(order_id: int, data: dict):
    database.assign_order(order_id, data.get("repartidorNombre"))
    return {"message": "Repartidor asignado"}