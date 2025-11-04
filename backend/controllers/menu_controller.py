from fastapi import APIRouter
import database

router = APIRouter(prefix="/api/menu", tags=["menu"])

@router.get("/")
def listar_platos():
    return list(database.dishes.values())