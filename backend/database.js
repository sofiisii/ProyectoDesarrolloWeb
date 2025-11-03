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
    // Tabla de Usuarios
    db.run(`
        CREATE TABLE IF NOT EXISTS User (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'cliente',
            categoria TEXT DEFAULT 'nuevo'
        )
    `, (err) => {
        if (err) console.error("Error creando tabla User:", err.message);
        else console.log("Tabla User lista.");
    });

    // Tabla de Productos (para el catálogo)
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
        else console.log("Tabla Product lista.");
    });
    
    // Aquí podrías agregar las tablas de Pedidos, etc.
});

module.exports = db;