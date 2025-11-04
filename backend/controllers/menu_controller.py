from fastapi import APIRouter, Header, HTTPException
from typing import Optional
from collections import defaultdict
import database

router = APIRouter(prefix="/api", tags=["Menú"])

# --- 🧾 Rutas públicas ---
@router.get("/menu")
def get_menu():
    """Devuelve todos los platos disponibles (público)."""
    return list(database.dishes.values())


@router.get("/menu/{dish_id}")
def get_dish(dish_id: int):
    """Devuelve un plato específico por ID."""
    dish = database.dishes.get(dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="Plato no encontrado")
    return dish


@router.post("/menu")
def add_dish(nombre: str, precio: float, categoria: str):
    """Agrega un nuevo plato (simulado)."""
    new_id = max(database.dishes.keys()) + 1 if database.dishes else 1
    dish = database.Dish(new_id, nombre, precio, categoria)
    database.dishes[new_id] = dish
    return {"message": "Plato agregado", "dish": dish}


# --- 👑 Rutas para administradores ---
@router.get("/admin/menu")
def get_admin_menu(Authorization: Optional[str] = Header(default=None)):
    """Devuelve el menú agrupado por categoría (solo admin)."""
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")

    token = Authorization.split(" ")[1]
    user = database.get_user_by_token(token)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")

    grouped = defaultdict(list)
    for dish in database.dishes.values():
        grouped[dish.categoria].append({
            "id": dish.id,
            "nombre": dish.nombre,
            "precio": dish.precio
        })

    result = [{"categoria": cat, "platos": items} for cat, items in grouped.items()]
    return result


@router.get("/products/admin")
def get_admin_products(Authorization: Optional[str] = Header(default=None)):
    """Alias compatible con el frontend: /api/products/admin (agrupado)."""
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")

    token = Authorization.split(" ")[1]
    user = database.get_user_by_token(token)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")

    grouped = defaultdict(list)
    for dish in database.dishes.values():
        grouped[dish.categoria].append({
            "id": dish.id,
            "nombre": dish.nombre,
            "precio": dish.precio
        })

    result = [{"categoria": cat, "platos": items} for cat, items in grouped.items()]
    return result