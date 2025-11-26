from pymongo import MongoClient
from typing import Optional, List, Dict
import uuid
import os

# --- Configuración de MongoDB ---
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
        "id": new_id, "nombre": nombre, "email": email, "password": password, "role": role
    }
    users_collection.insert_one(user_doc)
    return user_doc

def authenticate(email, password) -> Optional[dict]:
    user = users_collection.find_one({"email": email, "password": password})
    if user: user.pop("_id")
    return user

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
    return list(dishes_collection.find({}, {"_id": 0}))

def get_dish(dish_id: int):
    return dishes_collection.find_one({"id": dish_id}, {"_id": 0})

# ACTUALIZADO: Ahora soporta descripción, ingredientes y gradiente
def create_dish(nombre: str, precio: float, categoria: str, description: str = "", ingredients: str = "", gradient: str = ""):
    new_id = get_next_sequence("dishid")
    dish = {
        "id": new_id,
        "nombre": nombre,
        "precio": precio,
        "categoria": categoria,
        "description": description,
        "ingredients": ingredients,
        "gradient": gradient,
        "disponible": True
    }
    dishes_collection.insert_one(dish)
    return dish

def update_dish_availability(dish_id: int, available: bool):
    dishes_collection.update_one({"id": dish_id}, {"$set": {"disponible": available}})

# --- Funciones de Pedidos ---

def create_order(user_id: int, items: List[dict], total: float, estado: str, payment_method: str, delivery_address: str):
    new_id = get_next_sequence("orderid")
    order = {
        "id": new_id,
        "user_id": user_id,
        "items": items, # Ahora es una lista de objetos completos
        "total": total,
        "estado": estado,
        "payment_method": payment_method,
        "delivery_address": delivery_address
    }
    orders_collection.insert_one(order)
    order.pop("_id")
    return order


def get_all_orders():
    return list(orders_collection.find({}, {"_id": 0}))

def get_order_by_id(order_id: int):
    return orders_collection.find_one({"id": order_id}, {"_id": 0})

def update_order_status(order_id: int, status: str):
    orders_collection.update_one({"id": order_id}, {"$set": {"estado": status}})

def assign_order(order_id: int, repartidor_nombre: str):
    orders_collection.update_one({"id": order_id}, {"$set": {"repartidorNombre": repartidor_nombre, "estado": "en_ruta"}})

# --- Funciones de Reportes ---
def get_stats():
    # Cálculos básicos para dashboard
    pipeline_sales = [{"$group": {"_id": None, "total": {"$sum": "$total"}}}]
    sales_result = list(orders_collection.aggregate(pipeline_sales))
    total_sales = sales_result[0]["total"] if sales_result else 0
    
    return {
        "dailySales": total_sales,
        "activeOrders": orders_collection.count_documents({"estado": {"$in": ["pendiente", "preparando", "en_ruta"]}}),
        "newClients": users_collection.count_documents({"role": "cliente"}),
        "recentActivity": [] # Se puede implementar historial luego
    }

# --- Inicialización (Seed Data) ---
def seed_data():
    """Crea datos iniciales usando los datos REALES de tu catálogo"""
    if users_collection.count_documents({}) == 0:
        print("Seeding Admin User...")
        create_user("Admin", "admin@saborlimeno.com", "1234")
    
    if dishes_collection.count_documents({}) == 0:
        print("Seeding Menu con datos reales...")
        # Estos son los datos que tenías en el frontend, ahora van a la BD
        create_dish("Lomo Saltado", 12990, "fondo", 
                    "Trozos de filete de vacuno flambeados al wok...", 
                    "Filete de vacuno|Cebolla morada|Tomate|Papas fritas|Arroz blanco",
                    "linear-gradient(135deg, var(--terracota), #D84315)")
        
        create_dish("Ceviche Clásico", 10990, "entradas", 
                    "Fresco pescado blanco del día marinado en jugo de limón...", 
                    "Pescado blanco fresco|Limón de pica|Cebolla morada|Ají limo|Camote",
                    "linear-gradient(135deg, var(--azul-pacifico), #1976D2)")
        
        create_dish("Ají de Gallina", 11990, "fondo", 
                    "Pechuga de gallina deshilachada en una cremosa salsa...", 
                    "Pechuga de gallina|Crema de ají amarillo|Leche|Nueces|Queso parmesano",
                    "linear-gradient(135deg, var(--aji-amarillo), #FFB300)")
        
        create_dish("Causa Limeña", 8990, "entradas", 
                    "Suave puré de papa amarilla relleno de pollo...", 
                    "Papa amarilla|Limón|Pasta de ají amarillo|Pechuga de pollo|Mayonesa",
                    "linear-gradient(135deg, var(--verde-menta), #388E3C)")
        
        create_dish("Suspiro a la Limeña", 6500, "postres", 
                    "Una base de manjar blanco casero coronada por merengue...", 
                    "Leche evaporada|Leche condensada|Yemas de huevo|Vino Oporto|Canela",
                    "linear-gradient(135deg, var(--purpura-nazca), #8E24AA)")
        
        create_dish("Inca Kola 500ml", 1500, "postres", 
                    "Bebida gaseosa de sabor único.", 
                    "Agua carbonatada|Azúcar|Saborizantes",
                    "linear-gradient(135deg, var(--aji-amarillo), #FFB300)")
                    
        create_dish("Arroz con Pato", 13990, "fondo", 
                    "Clásico arroz verde norteño con pato tierno.", 
                    "Pato|Arroz|Cilantro|Cerveza negra",
                    "linear-gradient(135deg, var(--verde-menta), #388E3C)")

# Ejecutar seed al importar
seed_data()