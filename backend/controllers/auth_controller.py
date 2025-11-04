from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse
from typing import Optional
import database

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register")
def register(data: dict):
    user = database.create_user(data["nombre"], data["email"], data["password"])
    if not user:
        return JSONResponse(status_code=409, content={"message": "Correo ya registrado"})
    return {"message": "Registro exitoso"}

@router.post("/login")
def login(data: dict):
    user = database.authenticate(data["email"], data["password"])
    if not user:
        return JSONResponse(status_code=401, content={"message": "Credenciales incorrectas"})
    token = database.create_session(user.id)
    return {"token": token, "user": {"id": user.id, "nombre": user.nombre, "email": user.email, "role": user.role}}

@router.get("/me")
def me(Authorization: Optional[str] = Header(default=None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"message": "Token inválido"})

    token = Authorization.split(" ")[1]
    user = database.get_user_by_token(token)
    if not user:
        return JSONResponse(status_code=403, content={"message": "Token expirado"})

    return {
        "id": user.id,
        "nombre": user.nombre,
        "email": user.email,
        "role": user.role
    }