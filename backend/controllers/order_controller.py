from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from datetime import datetime
import database

# Definimos el router (esto corrige el error NameError)
router = APIRouter(prefix="/api/orders", tags=["orders"])

# --- Función auxiliar robusta para formatear pedidos ---
def format_order_response(order):
    client_name = "Cliente Invitado"
    client_email = "N/A"
    
    # Intentamos obtener datos del cliente si existe user_id
    if order.get("user_id"):
        user = database.users_collection.find_one({"id": order["user_id"]})
        if user:
            client_name = user.get("nombre", "Sin nombre")
            client_email = user.get("email", "Sin email")
            
    # Manejo seguro de fechas (para evitar error en la boleta)
    fecha_creacion = order.get("created_at")
    if not fecha_creacion:
        fecha_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        fecha_str = str(fecha_creacion)

    return {
        "id": order["id"],
        "createdAt": fecha_str,
        "totalAmount": order.get("total", 0),
        "status": order.get("estado", "pendiente"),
        "clientName": client_name,
        "clientEmail": client_email,
        "deliveryAddress": order.get("delivery_address", "Retiro en tienda"),
        "paymentMethod": order.get("payment_method", "Efectivo"),
        "items": [
            {
                "productName": item.get("name", "Producto"),
                "quantity": item.get("quantity", 0),
                "priceAtPurchase": item.get("price", 0)
            } for item in order.get("items", [])
        ],
        "repartidorNombre": order.get("repartidorNombre")
    }

@router.post("/")
def crear_pedido(data: dict, Authorization: Optional[str] = Header(default=None)):
    print("--- INTENTO DE CREAR PEDIDO ---") # Log en consola
    
    # 1. Validar Token
    if not Authorization or not Authorization.startswith("Bearer "):
        print("ERROR: No se recibió token válido")
        raise HTTPException(status_code=401, detail="Debes iniciar sesión")
    
    token = Authorization.split(" ")[1]
    user = database.get_user_by_token(token)
    
    if not user:
        print("ERROR: Token expirado o usuario no encontrado")
        raise HTTPException(status_code=403, detail="Sesión inválida")
        
    user_id = user["id"]
    print(f"USUARIO IDENTIFICADO: ID {user_id} ({user.get('nombre')})")

    # 2. Procesar items
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
        raise HTTPException(status_code=400, detail="El carrito está vacío o tiene productos inválidos")

    # 3. Guardar en BD
    try:
        pedido = database.create_order(
            user_id=user_id, 
            items=processed_items, 
            total=total_amount, 
            estado="pendiente", 
            payment_method=payment_method, 
            delivery_address=delivery_address
        )
        print(f"ÉXITO: Pedido #{pedido['id']} creado para usuario {user_id}")
        return {"message": "Pedido creado", "orderId": pedido["id"], "pedido": format_order_response(pedido)}
    except Exception as e:
        print(f"ERROR CRÍTICO AL GUARDAR EN BD: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/current")
def get_current_order(Authorization: Optional[str] = Header(default=None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
    
    token = Authorization.split(" ")[1]
    user = database.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=403, detail="Sesión expirada")
        
    print(f"BUSCANDO PEDIDO PARA: ID {user['id']}")
    order = database.get_latest_order_by_user(user["id"])
    
    if not order:
        print("NO SE ENCONTRÓ PEDIDO ACTIVO")
        raise HTTPException(status_code=404, detail="No tienes pedidos activos")
        
    print(f"PEDIDO ENCONTRADO: #{order['id']}")
    return format_order_response(order)

@router.get("/{order_id}")
def obtener_pedido(order_id: int):
    order = database.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return format_order_response(order)
    
@router.get("/")
def listar_pedidos():
    # Solo para debug/admin
    return [format_order_response(p) for p in database.get_all_orders()]

@router.patch("/{order_id}/status")
def update_status(order_id: int, data: dict):
    database.update_order_status(order_id, data.get("status"))
    return {"message": "Estado actualizado"}

@router.patch("/{order_id}/assign")
def assign_driver(order_id: int, data: dict):
    database.assign_order(order_id, data.get("repartidorNombre"))
    return {"message": "Repartidor asignado"}