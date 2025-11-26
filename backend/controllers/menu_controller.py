from fastapi import APIRouter, Header, HTTPException
from typing import Optional
from collections import defaultdict
import database 

router = APIRouter(prefix="/api", tags=["Menú"])

@router.get("/menu")
def get_menu():
    """Devuelve todos los platos desde MongoDB."""
    return database.get_all_dishes()

@router.get("/menu/{dish_id}")
def get_dish(dish_id: int):
    dish = database.get_dish(dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="Plato no encontrado")
    return dish

@router.post("/products") 
def add_dish(data: dict):
    # Ahora guardamos también la descripción e ingredientes si vienen
    dish = database.create_dish(
        data.get("name"), 
        data.get("price"), 
        data.get("category"),
        data.get("description", "Sin descripción"),
        data.get("ingredients", "Ingredientes no especificados"),
        data.get("gradient", "linear-gradient(135deg, #ccc, #999)")
    )
    return {"message": "Plato agregado", "dish": dish}

@router.patch("/products/{dish_id}/availability")
def update_availability(dish_id: int, data: dict):
    # Endpoint para el toggle de disponibilidad
    database.update_dish_availability(dish_id, data["available"])
    return {"message": "Disponibilidad actualizada"}

@router.get("/products/admin")
def get_admin_products(Authorization: Optional[str] = Header(default=None)):
    # Validación simple de token para admin
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
        
    # Aquí podrías validar el usuario real con database.get_user_by_token
    return database.get_all_dishes()