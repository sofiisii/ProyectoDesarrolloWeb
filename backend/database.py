from dataclasses import dataclass
from typing import Dict, List, Optional
import uuid

@dataclass
class User:
    id: int
    nombre: str
    email: str
    password: str
    role: str = "cliente"   # Campo de rol agregado

@dataclass
class Dish:
    id: int
    nombre: str
    precio: float
    categoria: str

@dataclass
class Order:
    id: int
    user_id: int
    items: List[int]
    total: float
    estado: str

@dataclass
class Payment:
    id: int
    order_id: int
    metodo: str
    monto: float
    confirmado: bool

# --- "Base de datos" en memoria ---
users: Dict[int, User] = {}
dishes: Dict[int, Dish] = {
    1: Dish(1, "Ceviche Mixto", 10.5, "Ceviches"),
    2: Dish(2, "Lomo Saltado", 12.0, "Platos Criollos"),
    3: Dish(3, "Arroz con Mariscos", 13.5, "Mariscos")
}
orders: Dict[int, Order] = {}
payments: Dict[int, Payment] = {}
sessions: Dict[str, int] = {}

_next_user_id = 1
_next_order_id = 1
_next_payment_id = 1

# --- Funciones de gestión de datos ---

def create_user(nombre, email, password) -> Optional[User]:
    global _next_user_id
    for u in users.values():
        if u.email == email:
            return None

    # Asignar rol automático según el email
    role = "admin" if email.endswith("@admin.com") else "cliente"

    user = User(_next_user_id, nombre, email, password, role)
    users[_next_user_id] = user
    _next_user_id += 1
    return user


def authenticate(email, password) -> Optional[User]:
    for u in users.values():
        if u.email == email and u.password == password:
            return u
    return None


def create_session(user_id: int) -> str:
    token = str(uuid.uuid4())
    sessions[token] = user_id
    return token


def get_user_by_token(token: str) -> Optional[User]:
    uid = sessions.get(token)
    if uid is not None and uid in users:
        return users[uid]
    return None


#--- Usuario administrador por defecto ---
default_admin = User(0, "Admin", "admin@sabor.admin.com", "1234", "admin")
users[0] = default_admin

#Crear sesión válida (token activo) para el admin
def create_admin_session():
    token = str(uuid.uuid4())
    sessions[token] = 0  # id del admin
    print("Usuario admin precargado:")
    print(f"   Email: {default_admin.email}")
    print(f"   Password: {default_admin.password}")
    print(f"   Token válido: {token}")
    return token

create_admin_session()