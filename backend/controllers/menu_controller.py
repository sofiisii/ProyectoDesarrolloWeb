from fastapi import APIRouter, Header, HTTPException, UploadFile, File, Form
from typing import Optional
from collections import Counter
import database 
import shutil
import os

router = APIRouter(prefix="/api", tags=["Menú"])

@router.get("/menu")
def get_menu():
    return database.get_all_dishes()

# --- NUEVO ENDPOINT: TOP 3 PLATOS MÁS VENDIDOS ---
@router.get("/menu/top")
def get_top_dishes():
    # 1. Obtener todas las órdenes y todos los platos
    orders = database.get_all_orders()
    all_dishes = database.get_all_dishes()
    
    if not orders:
        # Si no hay ventas, devolvemos los 3 primeros del menú como sugerencia
        return all_dishes[:3]

    # 2. Contar frecuencia de productos
    product_counts = Counter()
    for order in orders:
        # Solo contamos pedidos no anulados
        if order.get("estado") != "anulado":
            for item in order.get("items", []):
                # A veces se guarda como 'productId', a veces como 'id' dependiendo de la versión del código
                pid = item.get("productId") or item.get("id")
                qty = item.get("quantity", 1)
                if pid:
                    product_counts[pid] += qty
    
    # 3. Obtener los 3 IDs más comunes
    top_ids = [pid for pid, count in product_counts.most_common(3)]
    
    # 4. Buscar los detalles completos de esos platos
    top_dishes = []
    # Mapa rápido para buscar plato por ID
    dish_map = {d["id"]: d for d in all_dishes}
    
    for pid in top_ids:
        if pid in dish_map:
            top_dishes.append(dish_map[pid])
            
    # Si hay menos de 3 vendidos, rellenamos con otros del menú
    if len(top_dishes) < 3:
        for dish in all_dishes:
            if dish not in top_dishes:
                top_dishes.append(dish)
            if len(top_dishes) == 3:
                break
                
    return top_dishes

@router.get("/menu/{dish_id}")
def get_dish(dish_id: int):
    dish = database.get_dish(dish_id)
    if not dish:
        raise HTTPException(status_code=404, detail="Plato no encontrado")
    return dish

@router.post("/products") 
def add_dish(
    name: str = Form(...),
    price: int = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    image: UploadFile = File(...)
):
    upload_folder = "../frontend/imagenes"
    os.makedirs(upload_folder, exist_ok=True)
    file_location = f"{upload_folder}/{image.filename}"
    
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    image_url_db = f"imagenes/{image.filename}"

    dish = database.create_dish(
        nombre=name, 
        precio=price, 
        categoria=category,
        description=description,
        ingredients="Ingredientes no especificados",
        image=image_url_db
    )
    return {"message": "Plato agregado con imagen", "dish": dish}

@router.patch("/products/{dish_id}/availability")
def update_availability(dish_id: int, data: dict):
    database.update_dish_availability(dish_id, data["available"])
    return {"message": "Disponibilidad actualizada"}

@router.get("/products/admin")
def get_admin_products(Authorization: Optional[str] = Header(default=None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
    return database.get_all_dishes()

@router.get("/products/stats")
def get_menu_stats(Authorization: Optional[str] = Header(default=None)):
    if not Authorization or not Authorization.startswith("Bearer "):
         raise HTTPException(status_code=401, detail="Token inválido")
    all_dishes = database.get_all_dishes()
    total = len(all_dishes)
    disponibles = sum(1 for d in all_dishes if d.get("disponible", True))
    return { "total": total, "disponibles": disponibles, "no_disponibles": total - disponibles }