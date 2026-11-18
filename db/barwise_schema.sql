CREATE DATABASE IF NOT EXISTS barwise CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE barwise;

SET FOREIGN_KEY_CHECKS = 0;
DROP VIEW IF EXISTS v_sales_by_location;
DROP TABLE IF EXISTS audit_log, invoices, payments, order_items, orders, inventory_movements, inventory, supplier_products, suppliers, tables_bar, products, categories, sessions, users, roles, locations, payment_methods;
SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE roles (id TINYINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, name VARCHAR(30) NOT NULL UNIQUE);
CREATE TABLE payment_methods (id TINYINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, name VARCHAR(30) NOT NULL UNIQUE, active BOOLEAN NOT NULL DEFAULT TRUE);
CREATE TABLE locations (id SMALLINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, name VARCHAR(80) NOT NULL UNIQUE, address VARCHAR(180) NOT NULL, active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE users (id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, username VARCHAR(50) NOT NULL UNIQUE, full_name VARCHAR(120) NOT NULL, password_hash VARCHAR(255) NOT NULL, role_id TINYINT UNSIGNED NOT NULL, location_id SMALLINT UNSIGNED NULL, active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(role_id) REFERENCES roles(id), FOREIGN KEY(location_id) REFERENCES locations(id));
CREATE TABLE sessions (token CHAR(64) PRIMARY KEY, user_id BIGINT UNSIGNED NOT NULL, expires_at DATETIME NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE);
CREATE TABLE categories (id SMALLINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, name VARCHAR(80) NOT NULL UNIQUE, active BOOLEAN NOT NULL DEFAULT TRUE);
CREATE TABLE products (id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, code VARCHAR(40) NOT NULL UNIQUE, name VARCHAR(120) NOT NULL, category_id SMALLINT UNSIGNED NOT NULL, purchase_price DECIMAL(12,2) NOT NULL DEFAULT 0, sale_price DECIMAL(12,2) NOT NULL, active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(category_id) REFERENCES categories(id));
CREATE TABLE tables_bar (id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, location_id SMALLINT UNSIGNED NOT NULL, table_number SMALLINT UNSIGNED NOT NULL, seats TINYINT UNSIGNED NOT NULL, status ENUM('Libre','Ocupada') NOT NULL DEFAULT 'Libre', UNIQUE(location_id, table_number), FOREIGN KEY(location_id) REFERENCES locations(id));
CREATE TABLE inventory (location_id SMALLINT UNSIGNED NOT NULL, product_id BIGINT UNSIGNED NOT NULL, quantity DECIMAL(12,2) NOT NULL DEFAULT 0, minimum_quantity DECIMAL(12,2) NOT NULL DEFAULT 0, PRIMARY KEY(location_id, product_id), FOREIGN KEY(location_id) REFERENCES locations(id), FOREIGN KEY(product_id) REFERENCES products(id));
CREATE TABLE suppliers (id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, identification VARCHAR(40) NOT NULL UNIQUE, name VARCHAR(140) NOT NULL, country VARCHAR(80), city VARCHAR(80), phone VARCHAR(40), email VARCHAR(120), active BOOLEAN DEFAULT TRUE);
CREATE TABLE supplier_products (supplier_id BIGINT UNSIGNED NOT NULL, product_id BIGINT UNSIGNED NOT NULL, last_purchase_price DECIMAL(12,2) NOT NULL DEFAULT 0, PRIMARY KEY(supplier_id, product_id), FOREIGN KEY(supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE, FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE);
CREATE TABLE inventory_movements (id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, location_id SMALLINT UNSIGNED NOT NULL, product_id BIGINT UNSIGNED NOT NULL, user_id BIGINT UNSIGNED NOT NULL, type ENUM('Entrada','Salida') NOT NULL, quantity DECIMAL(12,2) NOT NULL, note VARCHAR(255), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(location_id) REFERENCES locations(id), FOREIGN KEY(product_id) REFERENCES products(id), FOREIGN KEY(user_id) REFERENCES users(id));
CREATE TABLE orders (id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, location_id SMALLINT UNSIGNED NOT NULL, table_id BIGINT UNSIGNED NOT NULL, waiter_id BIGINT UNSIGNED NOT NULL, status ENUM('Abierto','Pagado','Cerrado','Cancelado') NOT NULL DEFAULT 'Abierto', total DECIMAL(12,2) NOT NULL DEFAULT 0, opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, closed_at DATETIME NULL, FOREIGN KEY(location_id) REFERENCES locations(id), FOREIGN KEY(table_id) REFERENCES tables_bar(id), FOREIGN KEY(waiter_id) REFERENCES users(id));
CREATE TABLE order_items (id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, order_id BIGINT UNSIGNED NOT NULL, product_id BIGINT UNSIGNED NOT NULL, quantity DECIMAL(12,2) NOT NULL, unit_price DECIMAL(12,2) NOT NULL, FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE, FOREIGN KEY(product_id) REFERENCES products(id));
CREATE TABLE payments (id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, order_id BIGINT UNSIGNED NOT NULL UNIQUE, cashier_id BIGINT UNSIGNED NOT NULL, method ENUM('Efectivo','Credito','Debito') NOT NULL, amount DECIMAL(12,2) NOT NULL, paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(order_id) REFERENCES orders(id), FOREIGN KEY(cashier_id) REFERENCES users(id));
CREATE TABLE invoices (id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, order_id BIGINT UNSIGNED NOT NULL UNIQUE, invoice_number VARCHAR(40) NOT NULL UNIQUE, generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(order_id) REFERENCES orders(id));
CREATE TABLE audit_log (id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, user_id BIGINT UNSIGNED NULL, action VARCHAR(80) NOT NULL, entity VARCHAR(80) NOT NULL, entity_id BIGINT UNSIGNED NULL, details JSON NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL);

INSERT INTO roles(name) VALUES ('Administrador'),('Cajero'),('Mesero');
INSERT INTO payment_methods(name) VALUES ('Efectivo'),('Credito'),('Debito');
INSERT INTO locations(name,address) VALUES ('Calle 85','Calle 85 # 13-24'),('Galerias','Carrera 24 # 53-18');
INSERT INTO users(username,full_name,password_hash,role_id,location_id) VALUES
('admin','Administrador','barwise-demo-salt$29c5676822665b770cbf12fc236079058166b5b4b1ce0ceebafd723d42864fc8',1,NULL),
('cajero','Cajero Calle 85','barwise-demo-salt$29c5676822665b770cbf12fc236079058166b5b4b1ce0ceebafd723d42864fc8',2,1),
('mesero','Mesero Galerias','barwise-demo-salt$29c5676822665b770cbf12fc236079058166b5b4b1ce0ceebafd723d42864fc8',3,2);
INSERT INTO categories(name) VALUES ('Cervezas'),('Cocteles'),('Licores'),('Vinos');
INSERT INTO tables_bar(location_id,table_number,seats) VALUES (1,1,4),(1,2,2),(1,3,6),(2,1,4),(2,2,2),(2,3,4);
INSERT INTO products(code,name,category_id,purchase_price,sale_price) VALUES ('CER-001','Cerveza Artesanal',1,6000,12000),('GIN-001','Gin Tonic',2,13000,26000),('WHI-001','Whisky Old Fashioned',3,18000,29000),('VIN-001','Copa de Vino',4,7000,16000);
INSERT INTO inventory(location_id,product_id,quantity,minimum_quantity) SELECT l.id,p.id,48,10 FROM locations l CROSS JOIN products p WHERE p.code='CER-001';
INSERT INTO inventory(location_id,product_id,quantity,minimum_quantity) SELECT l.id,p.id,12,5 FROM locations l CROSS JOIN products p WHERE p.code='GIN-001';
INSERT INTO inventory(location_id,product_id,quantity,minimum_quantity) SELECT l.id,p.id,10,5 FROM locations l CROSS JOIN products p WHERE p.code='WHI-001';
INSERT INTO inventory(location_id,product_id,quantity,minimum_quantity) SELECT l.id,p.id,10,5 FROM locations l CROSS JOIN products p WHERE p.code='VIN-001';

CREATE OR REPLACE VIEW v_sales_by_location AS SELECT o.location_id, DATE(o.closed_at) sale_date, COUNT(*) orders_closed, SUM(o.total) total_sales FROM orders o WHERE o.status='Cerrado' GROUP BY o.location_id, DATE(o.closed_at);
CREATE OR REPLACE VIEW v_inventory_alerts AS SELECT i.location_id, i.product_id, p.name product_name, i.quantity, i.minimum_quantity FROM inventory i JOIN products p ON p.id=i.product_id WHERE i.quantity <= i.minimum_quantity;
CREATE OR REPLACE VIEW v_open_orders AS SELECT o.id, o.location_id, o.table_id, o.waiter_id, o.status, o.total, o.opened_at FROM orders o WHERE o.status IN ('Abierto','Pagado');

CREATE INDEX idx_users_location_role ON users(location_id, role_id, active);
CREATE INDEX idx_tables_location_status ON tables_bar(location_id, status);
CREATE INDEX idx_inventory_product ON inventory(product_id);
CREATE INDEX idx_orders_location_status_date ON orders(location_id, status, opened_at);
CREATE INDEX idx_movements_location_date ON inventory_movements(location_id, created_at);
