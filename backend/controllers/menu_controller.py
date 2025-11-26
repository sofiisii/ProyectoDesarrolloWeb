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

@router.post("/products") # Ojo: Ajusté la ruta para coincidir con tu frontend gestionmenu.html
def add_dish(data: dict):
    # Tu frontend envía JSON, así que usamos data: dict
    dish = database.create_dish(data["name"], data["price"], data["category"])
    return {"message": "Plato agregado", "dish": dish}

# Rutas de Admin
@router.get("/products/admin")
def get_admin_products(Authorization: Optional[str] = Header(default=None)):
    # ... (Mantén tu lógica de verificación de token aquí) ...
    
    # Cambia el acceso directo por la función
    all_dishes = database.get_all_dishes()
    
    # Tu lógica de agrupación se mantiene igual, pero iterando sobre la lista
    # Ojo: Asegúrate que las llaves coincidan con lo que guardaste en Mongo ("categoria" vs "category")
    return all_dishes # O aplica tu agrupación aquí