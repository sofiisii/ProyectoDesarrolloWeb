from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import database

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ... (Mantén tus funciones register, login y me igual que antes) ...

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
    
    token = database.create_session(user["id"])
    return {"token": token, "user": user}

@router.get("/me")
def me(Authorization: Optional[str] = Header(default=None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        return JSONResponse(status_code=401, content={"message": "Token inválido"})

    token = Authorization.split(" ")[1]
    user = database.get_user_by_token(token)
    if not user:
        return JSONResponse(status_code=403, content={"message": "Token expirado"})
    return user

# --- NUEVO: Endpoint para listar clientes ---
@router.get("/clients")
def get_clients(Authorization: Optional[str] = Header(default=None)):
    # Verificar si es admin
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
    
    token = Authorization.split(" ")[1]
    admin_user = database.get_user_by_token(token)
    
    if not admin_user or admin_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Requiere permisos de administrador")

    # Buscar todos los usuarios que sean 'cliente'
    clients = list(database.users_collection.find({"role": "cliente"}, {"_id": 0, "password": 0}))
    return clients