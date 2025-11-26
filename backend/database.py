from pymongo import MongoClient
from typing import Optional, List, Dict
import uuid
import os

# --- Configuración de MongoDB ---
# Si usas Docker o Atlas, cambia esta URL.
MONGO_URI = "mongodb://localhost:27017" 
client = MongoClient(MONGO_URI)
db = client["sabor_limeno_db"]

# Colecciones
users_collection = db["users"]
dishes_collection = db["dishes"]
orders_collection = db["orders"]
payments_collection = db["payments"]
sessions_collection = db["sessions"]
counters_collection = db["counters"]

# --- Helper para IDs autoincrementables ---
def get_next_sequence(sequence_name):
    """Genera IDs numéricos (1, 2, 3) como lo espera tu frontend"""
    counter = counters_collection.find_one_and_update(
        {"_id": sequence_name},
        {"$inc": {"sequence_value": 1}},
        upsert=True,
        return_document=True
    )
    return counter["sequence_value"]

# --- Funciones de Usuarios ---

def create_user(nombre, email, password) -> Optional[dict]:
    if users_collection.find_one({"email": email}):
        return None

    role = "admin" if email.endswith("@saborlimeno.com") else "cliente"
    new_id = get_next_sequence("userid")
    
    user_doc = {
        "id": new_id,
        "nombre": nombre,
        "email": email,
        "password": password,
        "role": role
    }
    users_collection.insert_one(user_doc)
    return user_doc

def authenticate(email, password) -> Optional[dict]:
    user = users_collection.find_one({"email": email, "password": password})
    if user:
        user.pop("_id") # Quitamos el _id de mongo para no romper pydantic/frontend
        return user
    return None

def create_session(user_id: int) -> str:
    token = str(uuid.uuid4())
    sessions_collection.insert_one({"token": token, "user_id": user_id})
    return token

def get_user_by_token(token: str) -> Optional[dict]:
    session = sessions_collection.find_one({"token": token})
    if session:
        user = users_collection.find_one({"id": session["user_id"]})
        if user:
            user.pop("_id")
            return user
    return None

# --- Funciones de Menú (Platos) ---

def get_all_dishes():
    dishes = list(dishes_collection.find({}, {"_id": 0}))
    return dishes

def get_dish(dish_id: int):
    return dishes_collection.find_one({"id": dish_id}, {"_id": 0})

def create_dish(nombre: str, precio: float, categoria: str):
    new_id = get_next_sequence("dishid")
    dish = {
        "id": new_id,
        "nombre": nombre,
        "precio": precio,
        "categoria": categoria,
        "disponible": True # Agregamos campo para el toggle
    }
    dishes_collection.insert_one(dish)
    return dish

# --- Funciones de Pedidos ---

def create_order(user_id: int, items: List[int], total: float, estado: str = "pendiente"):
    new_id = get_next_sequence("orderid")
    order = {
        "id": new_id,
        "user_id": user_id,
        "items": items, # Lista de IDs de platos
        "total": total,
        "estado": estado
    }
    orders_collection.insert_one(order)
    return order

def get_all_orders():
    return list(orders_collection.find({}, {"_id": 0}))

def get_order_by_id(order_id: int):
    return orders_collection.find_one({"id": order_id}, {"_id": 0})

def update_order_status(order_id: int, status: str):
    orders_collection.update_one({"id": order_id}, {"$set": {"estado": status}})

# --- Funciones de Reportes ---
def get_stats():
    return {
        "total_pedidos": orders_collection.count_documents({}),
        "total_usuarios": users_collection.count_documents({}),
        # Suma compleja en mongo, usamos una sencilla en python por ahora
        "ingresos_totales": sum(o['total'] for o in orders_collection.find()),
        "platos_disponibles": dishes_collection.count_documents({"disponible": True})
    }

# --- Inicialización (Seed Data) ---
def seed_data():
    """Crea datos iniciales si la base de datos está vacía"""
    if users_collection.count_documents({}) == 0:
        print("Seeding Admin User...")
        create_user("Admin", "admin@sabor.admin.com", "1234")
    
    if dishes_collection.count_documents({}) == 0:
        print("Seeding Menu...")
        # Insertamos usando la función create_dish para generar IDs
        create_dish("Ceviche Mixto", 10500, "entradas")
        create_dish("Lomo Saltado", 12990, "fondo")
        create_dish("Arroz con Mariscos", 13500, "especialidades")
        create_dish("Suspiro Limeño", 4500, "postres")

# Ejecutar seed al importar
seed_data()