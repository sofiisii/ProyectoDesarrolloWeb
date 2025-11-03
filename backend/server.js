const express = require('express');
const cors = require('cors');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const db = require('./database.js');

const app = express();
const PORT = 3000;
const SECRET_KEY = 'tu-clave-secreta-muy-segura'; // Cambia esto en un proyecto real

// Middlewares
app.use(cors()); // Permite que tu HTML se comunique con este servidor
app.use(express.json()); // Permite leer JSON del frontend

// --- ENDPOINTS DE AUTENTICACIÓN ---

// 1. Registro de Usuario (para Registro.html)
app.post('/api/auth/register', (req, res) => {
    const { nombre, email, password } = req.body;

    if (!nombre || !email || !password) {
        return res.status(400).json({ message: "Todos los campos son obligatorios." });
    }

    // Hashear la contraseña
    bcrypt.hash(password, 10, (err, hash) => {
        if (err) {
            return res.status(500).json({ message: "Error al hashear la contraseña." });
        }

        const sql = "INSERT INTO User (nombre, email, password, role, categoria) VALUES (?, ?, ?, 'cliente', 'nuevo')";
        db.run(sql, [nombre, email, hash], function(err) {
            if (err) {
                if (err.message.includes("UNIQUE constraint failed: User.email")) {
                    return res.status(409).json({ message: "Este correo ya está en uso" });
                }
                return res.status(500).json({ message: "Error al registrar el usuario." });
            }
            res.status(201).json({ message: "¡Registro y validación exitosa!", userId: this.lastID });
        });
    });
});

// 2. Login de Usuario (para signin.html)
app.post('/api/auth/login', (req, res) => {
    const { email, password } = req.body;

    if (!email || !password) {
        return res.status(400).json({ message: "Email y contraseña son obligatorios." });
    }

    const sql = "SELECT * FROM User WHERE email = ?";
    db.get(sql, [email], (err, user) => {
        if (err) {
            return res.status(500).json({ message: "Error del servidor." });
        }
        if (!user) {
            return res.status(404).json({ message: "Credenciales incorrectas." }); // No decimos "usuario no existe" por seguridad
        }

        // Comparar contraseña
        bcrypt.compare(password, user.password, (err, isMatch) => {
            if (err) {
                return res.status(500).json({ message: "Error al comparar contraseñas." });
            }
            if (!isMatch) {
                return res.status(401).json({ message: "Credenciales incorrectas." });
            }

            // Si todo es correcto, crear un Token (JWT)
            const token = jwt.sign(
                { id: user.id, email: user.email, role: user.role },
                SECRET_KEY,
                { expiresIn: '8h' } // El token expira en 8 horas
            );

            res.json({ 
                message: "Login exitoso", 
                token: token,
                user: {
                    email: user.email,
                    nombre: user.nombre,
                    role: user.role
                }
            });
        });
    });
});

// 3. Middleware para verificar el token en rutas protegidas
const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1]; // Formato "Bearer TOKEN"

    if (token == null) {
        return res.sendStatus(401); // No hay token
    }

    jwt.verify(token, SECRET_KEY, (err, user) => {
        if (err) {
            return res.sendStatus(403); // Token inválido o expirado
        }
        req.user = user;
        next();
    });
};

// 4. Ruta protegida de ejemplo (para saber quién soy)
app.get('/api/auth/me', authenticateToken, (req, res) => {
    // req.user fue establecido por el middleware authenticateToken
    // Devolvemos los datos del usuario sin la contraseña
    const sql = "SELECT id, nombre, email, role, categoria FROM User WHERE id = ?";
    db.get(sql, [req.user.id], (err, user) => {
        if (err) {
            return res.status(500).json({ message: "Error al buscar el usuario." });
        }
        if (!user) {
            return res.status(404).json({ message: "Usuario no encontrado." });
        }
        res.json(user);
    });
});


// --- ENDPOINTS DE PRODUCTOS (Ejemplo para catalogo.html) ---

// Devuelve solo productos disponibles
app.get('/api/products', (req, res) => {
    const sql = "SELECT * FROM Product WHERE disponible = true";
    db.all(sql, [], (err, rows) => {
        if (err) {
            return res.status(500).json({ message: "Error al cargar productos." });
        }
        res.json(rows);
    });
});


// Iniciar el servidor
app.listen(PORT, () => {
    console.log(`Servidor corriendo en http://localhost:${PORT}`);
});