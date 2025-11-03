const sqlite3 = require('sqlite3').verbose();

// Crea (o abre) el archivo de la base de datos
const db = new sqlite3.Database('./saborlimeno.db', (err) => {
    if (err) {
        console.error(err.message);
    }
    console.log('Conectado a la base de datos SQLite.');
});

// Crea las tablas si no existen
db.serialize(() => {
    // 1. Tabla de Usuarios (con nuevas columnas para reseteo Y fecha de creación)
    db.run(`
        CREATE TABLE IF NOT EXISTS User (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'cliente',
            categoria TEXT DEFAULT 'nuevo',
            
            resetToken TEXT,
            resetTokenExpires DATETIME,
            
            createdAt DATETIME DEFAULT CURRENT_TIMESTAMP 
        )
    `, (err) => {
        if (err) console.error("Error creando tabla User:", err.message);
        else console.log("Tabla User lista.");
    });

    // 2. Tabla de Productos
    db.run(`
        CREATE TABLE IF NOT EXISTS Product (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT,
            description TEXT,
            ingredients TEXT,
            disponible BOOLEAN DEFAULT true
        )
    `, (err) => {
        if (err) console.error("Error creando tabla Product:", err.message);
        else {
            console.log("Tabla Product lista.");
            populateProducts(); // Llama a poblar productos
        }
    });
    
    // 3. Tabla de Pedidos (Orders)
    db.run(`
        CREATE TABLE IF NOT EXISTS Orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userId INTEGER NOT NULL,
            totalAmount REAL NOT NULL,
            status TEXT DEFAULT 'pendiente', 
            createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
            deliveryAddress TEXT,
            paymentMethod TEXT,
            repartidorNombre TEXT, 
            FOREIGN KEY (userId) REFERENCES User(id)
        )
    `, (err) => {
        if (err) console.error("Error creando tabla Orders:", err.message);
        else console.log("Tabla Orders lista.");
    });
    
    // 4. Tabla de Items del Pedido (OrderItems)
    db.run(`
        CREATE TABLE IF NOT EXISTS OrderItems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orderId INTEGER NOT NULL,
            productId INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            priceAtPurchase REAL NOT NULL,
            FOREIGN KEY (orderId) REFERENCES Orders(id),
            FOREIGN KEY (productId) REFERENCES Product(id)
        )
    `, (err) => {
        if (err) console.error("Error creando tabla OrderItems:", err.message);
        else console.log("Tabla OrderItems lista.");
    });

});

// (Función de poblar productos - sin cambios)
function populateProducts() {
    const initialMenu = [
        { id: 1, name: 'Ceviche Clásico', price: 10990, category: 'entradas', disponible: true, description: "Pescado fresco marinado en limón.", ingredients: "Pescado|Limón|Cebolla" },
        { id: 2, name: 'Tiradito de Pescado', price: 11990, category: 'entradas', disponible: true, description: "Finas láminas de pescado.", ingredients: "Pescado|Ají Amarillo|Limón" },
        { id: 3, name: 'Causa Limeña', price: 8990, category: 'entradas', disponible: true, description: "Puré de papa amarilla con pollo.", ingredients: "Papa|Pollo|Mayonesa" },
        { id: 4, name: 'Lomo Saltado', price: 12990, category: 'fondo', disponible: true, description: "Trozos de carne salteados.", ingredients: "Carne|Cebolla|Tomate|Papas Fritas" },
        { id: 5, name: 'Ají de Gallina', price: 11990, category: 'fondo', disponible: false, description: "Crema de ají con gallina.", ingredients: "Gallina|Ají Amarillo|Leche|Pan" },
        { id: 6, name: 'Pachamanca', price: 14990, category: 'fondo', disponible: false, description: "Carnes cocidas bajo tierra.", ingredients: "Cerdo|Pollo|Camote" },
        { id: 7, name: 'Arroz con Pato', price: 13990, category: 'fondo', disponible: true, description: "Arroz verde con pato.", ingredients: "Pato|Arroz|Cilantro" },
        { id: 8, name: 'Anticuchos', price: 9990, category: 'especialidades', disponible: true, description: "Brochetas de corazón.", ingredients: "Corazón de Res|Ají Panca" },
        { id: 9, name: 'Rocoto Relleno', price: 12990, category: 'especialidades', disponible: false, description: "Rocoto con carne molida.", ingredients: "Rocoto|Carne|Queso" },
        { id: 10, name: 'Cuy Chactado', price: 18990, category: 'especialidades', disponible: true, description: "Cuy frito crujiente.", ingredients: "Cuy|Maíz|Papas" },
        { id: 11, name: 'Suspiro Limeño', price: 8990, category: 'postres', disponible: true, description: "Dulce de leche con merengue.", ingredients: "Leche condensada|Huevo|Vainilla" },
        { id: 12, name: 'Mazamorra Morada', price: 7990, category: 'postres', disponible: true, description: "Postre de maíz morado.", ingredients: "Maíz Morado|Frutas" },
        { id: 13, name: 'Picarones', price: 6990, category: 'postres', disponible: true, description: "Anillos fritos con miel.", ingredients: "Zapallo|Camote|Miel de Chancaca" }
    ];

    const checkSql = "SELECT COUNT(*) as count FROM Product";
    db.get(checkSql, [], (err, row) => {
        if (err) return console.error(err.message);
        
        if (row.count === 0) {
            console.log("Poblando base de datos con productos iniciales...");
            const insertSql = `INSERT INTO Product (id, name, price, category, disponible, description, ingredients) VALUES (?, ?, ?, ?, ?, ?, ?)`;
            
            const stmt = db.prepare(insertSql);
            initialMenu.forEach(dish => {
                stmt.run(dish.id, dish.name, dish.price, dish.category, dish.disponible, dish.description, dish.ingredients);
            });
            stmt.finalize((err) => {
                if(err) console.error("Error poblando productos:", err.message);
                else console.log("Productos iniciales insertados.");
            });
        } else {
            console.log("La tabla de productos ya tiene datos.");
        }
    });
}

module.exports = db;