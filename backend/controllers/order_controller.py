from fastapi import APIRouter
import database

router = APIRouter(prefix="/api/orders", tags=["orders"])

@router.post("/")
def crear_pedido(data: dict):
    global _next_order_id
    user_id = data["user_id"]
    items = data["items"]
    total = sum(database.dishes[i].precio for i in items)
    pedido = database.Order(database._next_order_id, user_id, items, total, "pendiente")
    database.orders[database._next_order_id] = pedido
    database._next_order_id += 1
    return {"message": "Pedido creado", "pedido": pedido.__dict__}

@router.get("/")
def listar_pedidos():
    return [o.__dict__ for o in database.orders.values()]