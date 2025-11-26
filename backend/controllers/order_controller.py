@router.post("/")
def crear_pedido(data: dict):
    user_id = data.get("user_id") # Ojo: Tu frontend envía user_id? A veces viene del token
    items_ids = data["items"] # IDs de los platos
    
    # Calcular total buscando precios en la BD
    total = 0
    for item_id in items_ids:
        dish = database.get_dish(item_id)
        if dish:
            total += dish["precio"]
            
    pedido = database.create_order(user_id, items_ids, total, "pendiente")
    return {"message": "Pedido creado", "pedido": pedido}

@router.get("/")
def listar_pedidos():
    return database.get_all_orders()