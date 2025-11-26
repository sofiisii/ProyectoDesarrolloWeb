from fastapi import APIRouter, Header, HTTPException
from typing import Optional
import database

# Creamos un router "vacío" para poder definir rutas con prefijos distintos manualmente
router = APIRouter()

# --- Función de seguridad auxiliar ---
def verify_admin(authorization: str):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
    token = authorization.split(" ")[1]
    user = database.get_user_by_token(token)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return user

# --- 1. Endpoint para el DASHBOARD (Corrige el error 404) ---
@router.get("/api/admin/dashboard", tags=["Admin"])
def get_admin_dashboard(Authorization: Optional[str] = Header(default=None)):
    """
    Este endpoint alimenta la pantalla principal de administración (administracion.html)
    """
    verify_admin(Authorization)
    # Llama a la función get_stats que definimos en database.py
    return database.get_stats()

# --- 2. Endpoints para la página de REPORTES (reporte.html) ---
@router.get("/api/reports/metrics", tags=["Reports"])
def get_metrics(period: str, Authorization: Optional[str] = Header(default=None)):
    verify_admin(Authorization)
    
    stats = database.get_stats()
    
    avg_ticket = 0
    if stats["dailySales"] > 0 and stats["activeOrders"] > 0:
        # Calculo simple simulado basado en datos disponibles
        avg_ticket = stats["dailySales"] / (stats["activeOrders"] + 1) 

    return {
        "totalSales": stats["dailySales"],
        "averageTicket": int(avg_ticket),
        "totalOrders": stats["activeOrders"]
    }

@router.get("/api/reports/top-products", tags=["Reports"])
def get_top_products(period: str, Authorization: Optional[str] = Header(default=None)):
    verify_admin(Authorization)
    
    # Pipeline para obtener los productos más vendidos desde MongoDB
    pipeline = [
        {"$unwind": "$items"},
        {"$group": {
            "_id": "$items.name",
            "totalQuantity": {"$sum": "$items.quantity"},
            "totalSales": {"$sum": {"$multiply": ["$items.price", "$items.quantity"]}}
        }},
        {"$sort": {"totalQuantity": -1}},
        {"$limit": 5}
    ]
    
    results = list(database.orders_collection.aggregate(pipeline))
    
    top_products = []
    for r in results:
        top_products.append({
            "name": r["_id"],
            "totalQuantity": r["totalQuantity"],
            "totalSales": r["totalSales"]
        })
        
    return top_products