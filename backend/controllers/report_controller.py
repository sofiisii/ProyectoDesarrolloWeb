from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from typing import Optional
import database

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/dashboard")
def get_admin_dashboard(Authorization: Optional[str] = Header(default=None)):
    # Verificar autenticación
    if not Authorization or not Authorization.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"message": "Token inválido"})

    token = Authorization.split(" ")[1]
    user = database.get_user_by_token(token)
    if not user or user.role != "admin":
        return JSONResponse(status_code=403, content={"message": "Acceso denegado"})

    # Datos simulados del dashboard
    stats = {
        "total_pedidos": len(database.orders),
        "total_usuarios": len(database.users),
        "ingresos_totales": sum(o.total for o in database.orders.values()) if database.orders else 0,
        "platos_disponibles": len(database.dishes),
    }

    return stats
