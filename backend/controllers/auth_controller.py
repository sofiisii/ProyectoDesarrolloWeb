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

# En login
@router.post("/login")
def login(data: dict):
    user = database.authenticate(data["email"], data["password"])
    if not user:
        return JSONResponse(status_code=401, content={"message": "Credenciales incorrectas"})
    
    token = database.create_session(user["id"]) # Nota: user["id"] no user.id
    return {"token": token, "user": user}

# En me
@router.get("/me")
def me(Authorization: Optional[str] = Header(default=None)):
    # ... validación token ...
    token = Authorization.split(" ")[1]
    user = database.get_user_by_token(token)
    if not user:
        return JSONResponse(status_code=403, content={"message": "Token expirado"})
    return user # Ya es un diccionario