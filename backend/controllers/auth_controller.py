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

# --- EN backend/controllers/auth_controller.py ---

@router.put("/clients/{user_id}")
def update_client(user_id: int, data: dict, Authorization: Optional[str] = Header(default=None)):
    # 1. Verificar seguridad (Solo admin)
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
    
    token = Authorization.split(" ")[1]
    admin_user = database.get_user_by_token(token)
    
    if not admin_user or admin_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Requiere permisos de administrador")

    # 2. Actualizar en BD
    database.update_user_details(user_id, data)
    
    return {"message": "Cliente actualizado correctamente"}

# --- También agregamos el DELETE para que el botón de borrar funcione ---
@router.delete("/clients/{user_id}")
def delete_client(user_id: int, Authorization: Optional[str] = Header(default=None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
    
    token = Authorization.split(" ")[1]
    admin_user = database.get_user_by_token(token)
    
    if not admin_user or admin_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Requiere permisos de administrador")

    # Eliminar de la colección
    database.users_collection.delete_one({"id": user_id})
    return {"message": "Cliente eliminado"}

# --- EN backend/controllers/auth_controller.py ---

# AGREGA ESTE BLOQUE COMPLETO:

@router.get("/clients")
def get_all_clients(Authorization: Optional[str] = Header(default=None)):
    """
    Endpoint para que el administrador vea la lista de todos los clientes.
    """
    # 1. Seguridad: Verificar que sea administrador
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
    
    token = Authorization.split(" ")[1]
    admin_user = database.get_user_by_token(token)
    
    # Usamos .get() por si acaso el campo 'role' no existe en usuarios antiguos
    if not admin_user or admin_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Requiere permisos de administrador")

    # 2. Obtener clientes de la base de datos
    # Filtramos para mostrar a todos los usuarios cuyo rol NO sea 'admin' (para ver solo clientes)
    clients_cursor = database.users_collection.find({"role": {"$ne": "admin"}})
    
    clients_list = []
    for user in clients_cursor:
        clients_list.append({
            "id": user["id"],
            "nombre": user["nombre"],
            "email": user["email"],
            # Si no tiene categoría, le ponemos 'nuevo' por defecto para que no falle el frontend
            "categoria": user.get("categoria", "nuevo")
        })
        
    return clients_list

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