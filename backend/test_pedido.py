import requests
import json
import random

# Configuración
API_URL = "http://localhost:8000"
EMAIL = "admin@saborlimeno.com" 
PASSWORD = "1234"

def crear_pedido_inteligente():
    print(f"\n--- 🤖 INICIANDO GENERADOR DE PEDIDOS ---")
    
    # 1. Iniciar Sesión
    print(f"🔑 1. Autenticando como {EMAIL}...")
    try:
        session = requests.Session()
        login_res = session.post(f"{API_URL}/api/auth/login", json={
            "email": EMAIL,
            "password": PASSWORD
        })
        
        if login_res.status_code != 200:
            print("❌ Error en login:", login_res.text)
            return

        token = login_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login exitoso.")

    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("👉 Asegúrate de que tu servidor esté corriendo (uvicorn main:app)")
        return

    # 2. Obtener Menú Real (Para conseguir IDs válidos)
    print("📋 2. Consultando menú para obtener productos reales...")
    try:
        menu_res = session.get(f"{API_URL}/api/menu", headers=headers)
        platos = menu_res.json()
        
        if not platos:
            print("❌ Error: El menú está vacío en la base de datos.")
            print("👉 Ejecuta 'seed_data()' en database.py o agrega platos manualmente.")
            return
            
        print(f"✅ Menú cargado: {len(platos)} platos disponibles.")
        
    except Exception as e:
        print(f"❌ Error al obtener menú: {e}")
        return

    # 3. Seleccionar Platos al Azar
    items_pedido = []
    cantidad_items = random.randint(1, 3) # Pedir entre 1 y 3 platos distintos
    
    # Elegimos platos al azar de la lista real
    platos_elegidos = random.sample(platos, min(len(platos), cantidad_items))
    
    print("\n🛒 3. Preparando carrito con:")
    for plato in platos_elegidos:
        cantidad = random.randint(1, 2)
        # Usamos la clave 'id' que viene de tu base de datos
        items_pedido.append({
            "productId": plato["id"], 
            "quantity": cantidad
        })
        print(f"   - {cantidad}x {plato['nombre']} (ID: {plato['id']})")

    # 4. Enviar el Pedido
    print("\n🚀 4. Enviando pedido al servidor...")
    pedido_payload = {
        "items": items_pedido,
        "paymentMethod": "Efectivo",
        "deliveryAddress": "Mesa de Prueba Automática"
    }
    
    try:
        order_res = session.post(f"{API_URL}/api/orders", json=pedido_payload, headers=headers)
        
        if order_res.status_code == 200:
            data = order_res.json()
            order_id = data["orderId"]
            print(f"\n✅ ¡ÉXITO! PEDIDO #{order_id} CREADO.")
            print("------------------------------------------------")
            print(f"👀 Ve AHORA a: http://localhost:8000/frontend/cocina.html")
            print("   El pedido debería aparecer en 'Comandas Activas'.")
            print("------------------------------------------------")
        else:
            print(f"❌ El servidor rechazó el pedido (Código {order_res.status_code}):")
            print(order_res.text)

    except Exception as e:
        print(f"❌ Error al enviar pedido: {e}")

if __name__ == "__main__":
    crear_pedido_inteligente()