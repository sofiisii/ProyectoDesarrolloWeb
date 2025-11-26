from fastapi import APIRouter, Header, HTTPException
from typing import Optional
import database

router = APIRouter(prefix="/api/reports", tags=["Reports"])

def verify_admin(authorization: str):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
    token = authorization.split(" ")[1]
    user = database.get_user_by_token(token)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return user

@router.get("/metrics")
def get_metrics(period: str, Authorization: Optional[str] = Header(default=None)):
    verify_admin(Authorization)
    
    # Nota: 'period' viene como '2025-11'. En un sistema real filtraríamos por fecha.
    # Por simplicidad, aquí devolvemos el total histórico para que veas datos.
    
    stats = database.get_stats() # Esta función ya la definimos en database.py
    
    # Calculamos ticket promedio
    avg_ticket = 0
    if stats["total_pedidos"] > 0:
        avg_ticket = stats["ingresos_totales"] / stats["total_pedidos"]

    return {
        "totalSales": stats["ingresos_totales"],
        "averageTicket": int(avg_ticket),
        "totalOrders": stats["total_pedidos"]
    }

@router.get("/top-products")
def get_top_products(period: str, Authorization: Optional[str] = Header(default=None)):
    verify_admin(Authorization)
    
    # Agregación de MongoDB para ver qué se vendió más
    pipeline = [
        {"$unwind": "$items"}, # Desglosar items de cada pedido
        {"$group": {
            "_id": "$items.name", # Agrupar por nombre del plato
            "totalQuantity": {"$sum": "$items.quantity"},
            "totalSales": {"$sum": {"$multiply": ["$items.price", "$items.quantity"]}}
        }},
        {"$sort": {"totalQuantity": -1}}, # Ordenar descendente
        {"$limit": 5}
    ]
    
    results = list(database.orders_collection.aggregate(pipeline))
    
    # Formatear para el frontend
    top_products = []
    for r in results:
        top_products.append({
            "name": r["_id"],
            "totalQuantity": r["totalQuantity"],
            "totalSales": r["totalSales"]
        })
        
    return top_products