from fastapi import APIRouter
import database

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/ventas")
def reporte_ventas():
    total = sum(p.total for p in database.orders.values())
    return {"total_ventas": total, "cantidad_pedidos": len(database.orders)}