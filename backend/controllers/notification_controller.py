from fastapi import APIRouter

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

@router.post("/")
def enviar_notificacion(data: dict):
    return {"message": f"Notificación enviada a {data.get('email', 'usuario desconocido')}"}