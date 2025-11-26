from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from typing import Optional
import database

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/dashboard")
def get_admin_dashboard(Authorization: Optional[str] = Header(default=None)):
    # ... validación token ...
    
    stats = database.get_stats() # Usamos la función nueva de database.py
    return stats
