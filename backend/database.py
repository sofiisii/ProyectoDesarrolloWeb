from pymongo import MongoClient
from typing import Optional, List, Dict
import uuid
import os
from datetime import datetime

# --- Configuración de MongoDB ---
MONGO_URI = "mongodb://localhost:27017" 
client = MongoClient(MONGO_URI)
db = client["sabor_limeno_db"]

# Colecciones
users_collection = db["users"]
dishes_collection = db["dishes"]
orders_collection = db["orders"]
payments_collection = db["payments"]
receipts_collection = db["receipts"]
sessions_collection = db["sessions"]
counters_collection = db["counters"]

# --- Helper para IDs ---
def get_next_sequence(sequence_name):
    counter = counters_collection.find_one_and_update(
        {"_id": sequence_name},
        {"$inc": {"sequence_value": 1}},
        upsert=True,
        return_document=True
    )
    return counter["sequence_value"]

# --- Usuarios ---
def create_user(nombre, email, password) -> Optional[dict]:
    if users_collection.find_one({"email": email}): return None
    role = "admin" if email.endswith("@saborlimeno.com") else "cliente"
    new_id = get_next_sequence("userid")
    user_doc = {"id": new_id, "nombre": nombre, "email": email, "password": password, "role": role, "categoria": "nuevo"}
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
        if user: user.pop("_id"); return user
    return None

def update_user_details(user_id: int, data: dict):
    update_data = {}
    if "nombre" in data: update_data["nombre"] = data["nombre"]
    if "email" in data: update_data["email"] = data["email"]
    if "categoria" in data: update_data["categoria"] = data["categoria"]
    users_collection.update_one({"id": user_id}, {"$set": update_data})
    return True

def update_password(email: str, new_password: str):
    result = users_collection.update_one({"email": email}, {"$set": {"password": new_password}})
    return result.modified_count > 0

# --- Menú (CON IMÁGENES) ---
def get_all_dishes():
    return list(dishes_collection.find({}, {"_id": 0}))

def get_dish(dish_id: int):
    return dishes_collection.find_one({"id": dish_id}, {"_id": 0})

# CAMBIO: Acepta 'image' y tiene un valor por defecto
def create_dish(nombre: str, precio: float, categoria: str, description: str = "", ingredients: str = "", image: str = ""):
    new_id = get_next_sequence("dishid")
    
    # Si no se pasa imagen, usamos un placeholder
    if not image:
        image = "https://placehold.co/600x400?text=Sin+Imagen"
        
    dish = {
        "id": new_id, "nombre": nombre, "precio": precio, "categoria": categoria,
        "description": description, "ingredients": ingredients, 
        "image": image, # Guardamos la ruta de la imagen
        "disponible": True
    }
    dishes_collection.insert_one(dish)
    return dish

def update_dish_availability(dish_id: int, available: bool):
    dishes_collection.update_one({"id": dish_id}, {"$set": {"disponible": available}})

# --- Pedidos ---
def create_order(user_id: int, items: List[dict], total: float, estado: str, payment_method: str, delivery_address: str, discount: float = 0, promo_name: str = ""):
    new_id = get_next_sequence("orderid")
    order = {
        "id": new_id, "user_id": user_id, "items": items, 
        "total": total, "original_total": total + discount, "discount": discount, "promo_name": promo_name,
        "estado": estado, "payment_method": payment_method, "delivery_address": delivery_address,
        "created_at": datetime.now()
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

def get_orders_by_user(user_id: int):
    return list(orders_collection.find({"user_id": user_id}, {"_id": 0}).sort("id", -1))

def get_latest_order_by_user(user_id: int):
    return orders_collection.find_one({"user_id": user_id}, sort=[("id", -1)], projection={"_id": 0})

# --- Boleta ---
def create_receipt(order_id: int, client_data: dict, items: list, total: float, payment_method: str):
    new_id = get_next_sequence("receiptid")
    receipt = {
        "id": new_id, "order_id": order_id, "rut_emisor": "76.123.456-7", "date": datetime.now(),
        "clientName": client_data.get("nombre", "Invitado"),
        "clientEmail": client_data.get("email", "N/A"),
        "clientAddress": client_data.get("address", "Retiro en tienda"),
        "products": items, "total": total, "paymentMethod": payment_method
    }
    receipts_collection.insert_one(receipt)
    receipt.pop("_id")
    return receipt

def get_receipt_by_order_id(order_id: int):
    return receipts_collection.find_one({"order_id": order_id}, {"_id": 0})

# --- Reportes ---
def get_stats():
    pipeline_sales = [{"$group": {"_id": None, "total": {"$sum": "$total"}}}]
    sales_result = list(orders_collection.aggregate(pipeline_sales))
    total_sales = sales_result[0]["total"] if sales_result else 0
    
    return {
        "dailySales": total_sales,
        "activeOrders": orders_collection.count_documents({"estado": {"$in": ["pendiente", "preparando", "en_ruta"]}}),
        "newClients": users_collection.count_documents({"role": "cliente"}),
        "recentActivity": [] 
    }

# --- SEED DATA (CON DESCIPCIONES REALES Y FOTOS) ---
def seed_data():
    # 1. Crear Admin si no existe
    if users_collection.count_documents({}) == 0:
        print("Seeding Admin User...")
        create_user("Admin", "admin@saborlimeno.com", "1234")
    
    # 2. Crear Platos si no existen
    if dishes_collection.count_documents({}) == 0:
        print("Seeding Menu con Descripciones Completas...")
        
        # Lomo Saltado
        create_dish(
            "Lomo Saltado", 12990, "fondo", 
            "Trozos de filete de vacuno salteados al wok con cebolla morada, tomate y salsa de soja. Acompañado de crujientes papas fritas y arroz blanco.",
            "Carne|Cebolla|Tomate|Papas Fritas|Arroz", 
            "imagenes/lomo saltado desarrollo web.jpg"
        )
        
        # Ceviche
        create_dish(
            "Ceviche Clásico", 10990, "entradas", 
            "Fresco pescado del día marinado en leche de tigre, limón de pica y ají limo. Servido con camote glaseado, choclo tierno y cancha serrana.", 
            "Pescado|Limón|Cebolla|Camote|Choclo", 
            "imagenes/ceviche clasico peruano desarrollo web.jpg"
        )
        
        # Ají de Gallina
        create_dish(
            "Ají de Gallina", 11990, "fondo", 
            "Pechuga de pollo deshilachada bañada en una cremosa salsa de ají amarillo, nueces y queso parmesano. Acompañado de papas, arroz y huevo.", 
            "Pollo|Ají Amarillo|Nueces|Queso|Arroz", 
            "imagenes/aji de gallina desarrollo web.jpg"
        )
        
        # Causa
        create_dish(
            "Causa Limeña", 8990, "entradas", 
            "Suave masa de papa amarilla prensada con limón y ají, rellena de palta fresca y pollo desmenuzado con mayonesa de la casa.", 
            "Papa|Pollo|Palta|Mayonesa|Limón", 
            "imagenes/causa limeña desarrollo web.jpg"
        )
        
        # Suspiro
        create_dish(
            "Suspiro a la Limeña", 6500, "postres", 
            "Clásico postre limeño. Manjar blanco de yemas cocinado lentamente, coronado con un merengue italiano al oporto y canela.", 
            "Leche|Yemas|Azúcar|Oporto|Canela", 
            "imagenes/suspiro limeño desarrollo web.jpg"
        )
        
        # Inca Kola
        create_dish(
            "Inca Kola 500ml", 1500, "postres", 
            "La bebida del sabor nacional. Gaseosa peruana dulce y refrescante con notas de hierba luisa, ideal para acompañar nuestros platos.", 
            "Soda", 
            "imagenes/inca kola desarrollo web.jpg"
        )
        
        # Arroz con Pato
        create_dish(
            "Arroz con Pato", 13990, "fondo", 
            "Arroz verde cocinado con cilantro y cerveza negra, servido con una pierna de pato confitada suave y jugosa, con salsa criolla.", 
            "Pato|Arroz|Cilantro|Cerveza|Cebolla", 
            "imagenes/arroz con pato desarrollo web.jpg"
        )

seed_data()