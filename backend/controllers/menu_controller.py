from fastapi import APIRouter, Header, HTTPException
from typing import Optional
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
    # Recibe datos del formulario (en inglés o español, adaptamos aquí)
    # El frontend envía: name, price, category
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
    database.update_dish_availability(dish_id, data["available"])
    return {"message": "Disponibilidad actualizada"}

@router.get("/products/admin")
def get_admin_products(Authorization: Optional[str] = Header(default=None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
    return database.get_all_dishes()

# --- NUEVO: Endpoint de estadísticas ---
@router.get("/products/stats")
def get_menu_stats(Authorization: Optional[str] = Header(default=None)):
    """Calcula totales para el panel de gestión"""
    # Validación básica de token
    if not Authorization or not Authorization.startswith("Bearer "):
         raise HTTPException(status_code=401, detail="Token inválido")
         
    all_dishes = database.get_all_dishes()
    total = len(all_dishes)
    # Contamos cuántos tienen disponible=True (asumiendo True si no existe el campo)
    disponibles = sum(1 for d in all_dishes if d.get("disponible", True))
    
    return {
        "total": total,
        "disponibles": disponibles,
        "no_disponibles": total - disponibles
    }