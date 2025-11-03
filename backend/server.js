const express = require('express');
const cors = require('cors');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const db = require('./database.js');
const crypto = require('crypto');

const app = express();
const PORT = 3000;
const SECRET_KEY = 'tu-clave-secreta-muy-segura';

// Middlewares
app.use(cors());
app.use(express.json());

// --- ENDPOINTS DE AUTENTICACIÓN ---
// 1. Registro
app.post('/api/auth/register', (req, res) => {
    const { nombre, email, password } = req.body;
    if (!nombre || !email || !password) {
        return res.status(400).json({ message: "Todos los campos son obligatorios." });
    }
    const role = (email === 'admin@saborlimeno.com') ? 'admin' : 'cliente';
    bcrypt.hash(password, 10, (err, hash) => {
        if (err) return res.status(500).json({ message: "Error al hashear la contraseña." });
        // Añadimos createdAt (aunque se pone por defecto, es buena práctica ser explícito)
        const sql = "INSERT INTO User (nombre, email, password, role, categoria, createdAt) VALUES (?, ?, ?, ?, 'nuevo', CURRENT_TIMESTAMP)";
        db.run(sql, [nombre, email, hash, role], function(err) {
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

// 2. Login
app.post('/api/auth/login', (req, res) => {
    // ... (Sin cambios)
    const { email, password } = req.body;
    if (!email || !password) return res.status(400).json({ message: "Email y contraseña son obligatorios." });
    const sql = "SELECT * FROM User WHERE email = ?";
    db.get(sql, [email], (err, user) => {
        if (err) return res.status(500).json({ message: "Error del servidor." });
        if (!user) return res.status(404).json({ message: "Credenciales incorrectas." });
        bcrypt.compare(password, user.password, (err, isMatch) => {
            if (err) return res.status(500).json({ message: "Error al comparar contraseñas." });
            if (!isMatch) return res.status(401).json({ message: "Credenciales incorrectas." });
            const token = jwt.sign(
                { id: user.id, email: user.email, role: user.role },
                SECRET_KEY, { expiresIn: '8h' }
            );
            res.json({ 
                message: "Login exitoso", token: token,
                user: { email: user.email, nombre: user.nombre, role: user.role }
            });
        });
    });
});

// --- MIDDLEWARES DE SEGURIDAD ---
// (3. Autenticar Token, 4. Verificar Admin, 5. Ruta "quién soy")
const authenticateToken = (req, res, next) => {
    // ... (Sin cambios)
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];
    if (token == null) return res.status(401).json({ message: "Token no proporcionado." });
    jwt.verify(token, SECRET_KEY, (err, user) => {
        if (err) return res.status(403).json({ message: "Token inválido o expirado." });
        req.user = user; next();
    });
};
const isAdmin = (req, res, next) => {
    // ... (Sin cambios)
    if (req.user.role !== 'admin') {
        return res.status(403).json({ message: "Acceso denegado. Requiere rol de administrador." });
    }
    next();
};
app.get('/api/auth/me', authenticateToken, (req, res) => {
    // ... (Sin cambios)
    const sql = "SELECT id, nombre, email, role, categoria FROM User WHERE id = ?";
    db.get(sql, [req.user.id], (err, user) => {
        if (err) return res.status(500).json({ message: "Error al buscar el usuario." });
        if (!user) return res.status(404).json({ message: "Usuario no encontrado." });
        res.json(user);
    });
});

// --- ENDPOINTS DE PRODUCTOS ---
// (endpoints 6, 7, 8, 9, 10 - Sin cambios)
app.get('/api/products', (req, res) => { db.all("SELECT * FROM Product WHERE disponible = true", [], (err, rows) => { if (err) return res.status(500).json({ message: "Error al cargar productos." }); res.json(rows); }); });
app.get('/api/products/admin', [authenticateToken, isAdmin], (req, res) => { db.all("SELECT * FROM Product", [], (err, rows) => { if (err) return res.status(500).json({ message: "Error al cargar productos para admin." }); res.json(rows); }); });
app.get('/api/products/stats', [authenticateToken, isAdmin], (req, res) => { const sql = `SELECT COUNT(*) as total, SUM(CASE WHEN disponible = 1 THEN 1 ELSE 0 END) as disponibles FROM Product`; db.get(sql, [], (err, row) => { if (err) return res.status(500).json({ message: "Error al calcular estadísticas." }); res.json({ total: row.total, disponibles: row.disponibles, no_disponibles: row.total - row.disponibles }); }); });
app.post('/api/products', [authenticateToken, isAdmin], (req, res) => { const { name, price, category } = req.body; if (!name || !price || !category) return res.status(400).json({ message: "Nombre, precio y categoría son obligatorios." }); const sql = "INSERT INTO Product (name, price, category, disponible, description, ingredients) VALUES (?, ?, ?, true, '', '')"; db.run(sql, [name, price, category], function(err) { if (err) return res.status(500).json({ message: "Error al crear el producto." }); res.status(201).json({ message: "Producto creado", id: this.lastID, name, price, category }); }); });
app.patch('/api/products/:id/availability', [authenticateToken, isAdmin], (req, res) => { const { id } = req.params; const { available } = req.body; if (typeof available !== 'boolean') return res.status(400).json({ message: "El estado 'available' (true/false) es obligatorio." }); const sql = "UPDATE Product SET disponible = ? WHERE id = ?"; db.run(sql, [available, id], function(err) { if (err) return res.status(500).json({ message: "Error al actualizar la disponibilidad." }); if (this.changes === 0) return res.status(404).json({ message: "Producto no encontrado." }); res.json({ message: "Disponibilidad actualizada." }); }); });

// --- ENDPOINTS DE PEDIDOS (Checkout y Boleta) ---
// (endpoints 11, 12 - Sin cambios)
app.post('/api/orders', authenticateToken, (req, res) => { const { items, totalAmount, paymentMethod, deliveryAddress } = req.body; const userId = req.user.id; if (!items || items.length === 0 || !totalAmount || !paymentMethod) { return res.status(400).json({ message: "Faltan datos para crear el pedido." }); } db.serialize(() => { db.run("BEGIN TRANSACTION"); const orderSql = `INSERT INTO Orders (userId, totalAmount, status, paymentMethod, deliveryAddress) VALUES (?, ?, 'pendiente', ?, ?)`; db.run(orderSql, [userId, totalAmount, paymentMethod, deliveryAddress || 'Av. Principal 123'], function(err) { if (err) { db.run("ROLLBACK"); return res.status(500).json({ message: "Error al crear la orden." }); } const orderId = this.lastID; const itemSql = `INSERT INTO OrderItems (orderId, productId, quantity, priceAtPurchase) VALUES (?, ?, ?, ?)`; const stmt = db.prepare(itemSql); let itemError = null; items.forEach(item => { stmt.run(orderId, item.productId, item.quantity, item.price, (err) => { if (err) itemError = err; }); }); stmt.finalize((err) => { if (err || itemError) { db.run("ROLLBACK"); return res.status(500).json({ message: "Error al guardar los items." }); } db.run("COMMIT", (err) => { if (err) return res.status(500).json({ message: "Error al confirmar." }); res.status(201).json({ message: "¡Pedido Confirmado!", orderId: orderId }); }); }); }); }); });
app.get('/api/orders/:id', authenticateToken, (req, res) => { const { id } = req.params; const userId = req.user.id; const userRole = req.user.role; const orderSql = `SELECT o.*, u.nombre as clientName, u.email as clientEmail, u.id as clientUserId FROM Orders o JOIN User u ON o.userId = u.id WHERE o.id = ?`; db.get(orderSql, [id], (err, order) => { if (err) return res.status(500).json({ message: "Error al buscar la orden." }); if (!order) return res.status(404).json({ message: "Orden no encontrada." }); if (order.clientUserId !== userId && userRole !== 'admin') { return res.status(403).json({ message: "No tienes permiso para ver esta orden." }); } const itemsSql = `SELECT oi.quantity, oi.priceAtPurchase, p.name as productName FROM OrderItems oi JOIN Product p ON oi.productId = p.id WHERE oi.orderId = ?`; db.all(itemsSql, [id], (err, items) => { if (err) return res.status(500).json({ message: "Error al buscar los items." }); res.json({ ...order, items: items }); }); }); });

// --- ENDPOINTS DE COCINA/DELIVERY ---
// (endpoints 13, 14 - Sin cambios)
app.patch('/api/orders/:id/status', [authenticateToken, isAdmin], (req, res) => { const { id } = req.params; const { status } = req.body; if (!status) return res.status(400).json({ message: "El 'status' es obligatorio." }); const validStatus = ['pendiente', 'preparando', 'completado', 'en_ruta', 'entregado', 'anulado']; if (!validStatus.includes(status)) return res.status(400).json({ message: "Estado no válido." }); const sql = "UPDATE Orders SET status = ? WHERE id = ?"; db.run(sql, [status, id], function(err) { if (err) return res.status(500).json({ message: "Error al actualizar el estado." }); if (this.changes === 0) return res.status(404).json({ message: "Pedido no encontrado." }); res.json({ message: `Pedido ${id} actualizado a '${status}'.` }); }); });
app.patch('/api/orders/:id/assign', [authenticateToken, isAdmin], (req, res) => { const { id } = req.params; const { repartidorNombre } = req.body; if (!repartidorNombre) return res.status(400).json({ message: "El 'repartidorNombre' es obligatorio." }); const sql = "UPDATE Orders SET status = 'en_ruta', repartidorNombre = ? WHERE id = ?"; db.run(sql, [repartidorNombre, id], function(err) { if (err) return res.status(500).json({ message: "Error al asignar el repartidor." }); if (this.changes === 0) return res.status(404).json({ message: "Pedido no encontrado." }); res.json({ message: `Pedido ${id} asignado a ${repartidorNombre} y puesto 'en_ruta'.` }); }); });

// --- ENDPOINTS DE REPORTES ---
// (endpoints 15, 16 - Sin cambios)
app.get('/api/reports/metrics', [authenticateToken, isAdmin], (req, res) => { const { period } = req.query; if (!period) return res.status(400).json({ message: "El 'period' (YYYY-MM) es obligatorio." }); const sql = `SELECT SUM(totalAmount) as totalSales, AVG(totalAmount) as averageTicket, COUNT(*) as totalOrders FROM Orders WHERE strftime('%Y-%m', createdAt) = ? AND status != 'anulado'`; db.get(sql, [period], (err, row) => { if (err) return res.status(500).json({ message: "Error al calcular métricas." }); if (!row || row.totalOrders === 0) return res.status(404).json({ message: "No hay datos para este periodo." }); res.json({ totalSales: row.totalSales || 0, averageTicket: row.averageTicket || 0, totalOrders: row.totalOrders || 0 }); }); });
app.get('/api/reports/top-products', [authenticateToken, isAdmin], (req, res) => { const { period } = req.query; if (!period) return res.status(400).json({ message: "El 'period' (YYYY-MM) es obligatorio." }); const sql = `SELECT p.name, SUM(oi.quantity) as totalQuantity, SUM(oi.priceAtPurchase * oi.quantity) as totalSales FROM OrderItems oi JOIN Orders o ON oi.orderId = o.id JOIN Product p ON oi.productId = p.id WHERE strftime('%Y-%m', o.createdAt) = ? AND o.status != 'anulado' GROUP BY p.name ORDER BY totalSales DESC LIMIT 5`; db.all(sql, [period], (err, rows) => { if (err) return res.status(500).json({ message: "Error al calcular top productos." }); res.json(rows); }); });

// --- ENDPOINTS DE GESTIÓN DE CLIENTES ---
// (endpoints 17, 18, 19 - Sin cambios)
app.get('/api/clients', [authenticateToken, isAdmin], (req, res) => { const sql = "SELECT id, nombre, email, categoria FROM User WHERE role = 'cliente'"; db.all(sql, [], (err, rows) => { if (err) return res.status(500).json({ message: "Error al obtener clientes." }); res.json(rows); }); });
app.put('/api/clients/:id', [authenticateToken, isAdmin], (req, res) => { const { id } = req.params; const { nombre, email, categoria } = req.body; if (!nombre || !email || !categoria) return res.status(400).json({ message: "Nombre, email y categoría son obligatorios." }); const sql = "UPDATE User SET nombre = ?, email = ?, categoria = ? WHERE id = ? AND role = 'cliente'"; db.run(sql, [nombre, email, categoria, id], function(err) { if (err) { if (err.message.includes("UNIQUE constraint failed")) return res.status(409).json({ message: "Ese email ya está en uso." }); return res.status(500).json({ message: "Error al actualizar cliente." }); } if (this.changes === 0) return res.status(404).json({ message: "Cliente no encontrado." }); res.json({ message: "Cliente actualizado." }); }); });
app.delete('/api/clients/:id', [authenticateToken, isAdmin], (req, res) => { const { id } = req.params; const sql = "DELETE FROM User WHERE id = ? AND role = 'cliente'"; db.run(sql, [id], function(err) { if (err) return res.status(500).json({ message: "Error al eliminar cliente. ¿Tiene pedidos asociados?" }); if (this.changes === 0) return res.status(404).json({ message: "Cliente no encontrado." }); res.json({ message: "Cliente eliminado." }); }); });

// --- ENDPOINTS DE RECUPERACIÓN DE CONTRASEÑA ---
// (endpoints 20, 21 - Sin cambios)
app.post('/api/auth/request-password-reset', (req, res) => { const { email } = req.body; if (!email) return res.status(400).json({ message: "Email es obligatorio." }); const sqlFind = "SELECT * FROM User WHERE email = ?"; db.get(sqlFind, [email], (err, user) => { if (err) return res.status(500).json({ message: "Error de servidor." }); if (!user) return res.status(404).json({ message: "No existe una cuenta asociada a este correo." }); const token = crypto.randomBytes(32).toString('hex'); const expires = new Date(Date.now() + 3600000); const sqlUpdate = "UPDATE User SET resetToken = ?, resetTokenExpires = ? WHERE id = ?"; db.run(sqlUpdate, [token, expires.toISOString(), user.id], function(err) { if (err) return res.status(500).json({ message: "Error al guardar el token." }); console.log(`TOKEN DE RESETEO (para ${email}): ${token}`); res.json({ message: "¡Enlace enviado! Revisa tu correo electrónico.", simulatedToken: token }); }); }); });
app.post('/api/auth/reset-password', (req, res) => { const { token, newPassword } = req.body; if (!token || !newPassword) return res.status(400).json({ message: "Token y nueva contraseña son obligatorios." }); const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/; if (!passwordRegex.test(newPassword)) { return res.status(400).json({ message: "La contraseña debe tener al menos 8 caracteres, una mayúscula y un número." }); } const sqlFind = "SELECT * FROM User WHERE resetToken = ? AND resetTokenExpires > ?"; db.get(sqlFind, [token, new Date().toISOString()], (err, user) => { if (err) return res.status(500).json({ message: "Error de servidor." }); if (!user) return res.status(400).json({ message: "Enlace caducado o inválido." }); bcrypt.hash(newPassword, 10, (err, hash) => { if (err) return res.status(500).json({ message: "Error al hashear." }); const sqlUpdate = "UPDATE User SET password = ?, resetToken = NULL, resetTokenExpires = NULL WHERE id = ?"; db.run(sqlUpdate, [hash, user.id], function(err) { if (err) return res.status(500).json({ message: "Error al actualizar." }); res.json({ message: "¡Recuperación exitosa! Tu contraseña ha sido actualizada." }); }); }); }); });

// --- NUEVO: ENDPOINT DEL DASHBOARD DE ADMIN ---

// Función helper para consultas de DB con promesas (facilita Promise.all)
function dbGet(sql, params) {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => {
            if (err) reject(err);
            resolve(row);
        });
    });
}
function dbAll(sql, params) {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => {
            if (err) reject(err);
            resolve(rows);
        });
    });
}

// 22. OBTENER Métricas del Dashboard (Admin)
app.get('/api/admin/dashboard', [authenticateToken, isAdmin], async (req, res) => {
    try {
        const today = new Date().toISOString().split('T')[0]; // 'YYYY-MM-DD'
        const thisMonth = new Date().toISOString().substring(0, 7); // 'YYYY-MM'

        // 1. Ventas del Día
        const salesSql = `SELECT SUM(totalAmount) as totalSales FROM Orders WHERE DATE(createdAt) = ? AND status != 'anulado'`;
        const salesPromise = dbGet(salesSql, [today]);

        // 2. Pedidos Activos
        const activeOrdersSql = `SELECT COUNT(*) as activeOrders FROM Orders WHERE status IN ('pendiente', 'preparando', 'completado', 'en_ruta')`;
        const activeOrdersPromise = dbGet(activeOrdersSql, []);

        // 3. Nuevos Clientes (este mes)
        const newClientsSql = `SELECT COUNT(*) as newClients FROM User WHERE STRFTIME('%Y-%m', createdAt) = ? AND role = 'cliente'`;
        const newClientsPromise = dbGet(newClientsSql, [thisMonth]);

        // 4. Actividad Reciente (últimos 4 pedidos)
        const activitySql = `
            SELECT o.id, o.status, o.totalAmount, u.nombre 
            FROM Orders o 
            JOIN User u ON o.userId = u.id 
            ORDER BY o.createdAt DESC 
            LIMIT 4
        `;
        const activityPromise = dbAll(activitySql, []);

        // Ejecutar todas las consultas en paralelo
        const [salesData, activeOrdersData, newClientsData, activityData] = await Promise.all([
            salesPromise,
            activeOrdersPromise,
            newClientsPromise,
            activityPromise
        ]);
        
        // (El rating es estático ya que no tenemos tabla de ratings)
        res.json({
            dailySales: salesData.totalSales || 0,
            activeOrders: activeOrdersData.activeOrders || 0,
            newClients: newClientsData.newClients || 0,
            recentActivity: activityData
        });

    } catch (error) {
        console.error("Error generando dashboard:", error);
        res.status(500).json({ message: "Error al cargar los datos del dashboard." });
    }
});


// Iniciar el servidor
app.listen(PORT, () => {
    console.log(`Servidor corriendo en http://localhost:${PORT}`);
    console.log("---");
    console.log("Para probar la parte de Admin, regístrate con el email: admin@saborlimeno.com");
    console.log("Cualquier otra cuenta será 'cliente'.");
    console.log("---");
});