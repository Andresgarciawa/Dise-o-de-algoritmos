"""API inicial de BarWise usando solamente la biblioteca estandar de Python."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from io import BytesIO
import json
import hashlib
import mysql.connector
from openpyxl import Workbook
try:
    from .mysql_repository import load_state, load_suppliers, load_products
    from .auth_service import public_user, login, user_from_session, logout, configure
    from .security import password_hash
    from .algorithms import (binary_search_products, merge_sort_products,
                             inventory_alerts, calculate_order_total, sales_summary,
                             linear_search_products, quick_sort_orders,
                             consolidate_order_items, paginate, calculate_change,
                             inventory_projection, top_selling_products)
except ImportError:
    from mysql_repository import load_state, load_suppliers, load_products
    from auth_service import public_user, login, user_from_session, logout, configure
    from security import password_hash
    from algorithms import (binary_search_products, merge_sort_products,
                            inventory_alerts, calculate_order_total, sales_summary,
                            linear_search_products, quick_sort_orders,
                            consolidate_order_items, paginate, calculate_change,
                            inventory_projection, top_selling_products)
try:
    from .mysql_database import check_connection
    from .mysql_database import connection
except ImportError:
    from mysql_database import check_connection
    from mysql_database import connection

HOST, PORT = '127.0.0.1', 5001

USERS, LOCATIONS, TABLES, PRODUCTS, ORDERS = load_state()
SESSIONS = {}
configure(USERS, SESSIONS)
NEXT_ORDER = max((order['id'] for order in ORDERS), default=0) + 1

def json_body(handler):
    try:
        length = int(handler.headers.get('Content-Length', 0))
        return json.loads(handler.rfile.read(length) or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        raise ValueError('El cuerpo debe ser JSON valido')

def audit(cur, user_id, action, entity, entity_id=None, details=None):
    cur.execute(
        'INSERT INTO audit_log(user_id,action,entity,entity_id,details) VALUES(%s,%s,%s,%s,%s)',
        (user_id, action, entity, entity_id, json.dumps(details, ensure_ascii=False) if details is not None else None)
    )

def sales_report(location_id, date_from='', date_to=''):
    for value in (date_from, date_to):
        if value:
            try:
                datetime.strptime(value, '%Y-%m-%d')
            except ValueError as error:
                raise ValueError('Las fechas deben tener el formato AAAA-MM-DD') from error
    if date_from and date_to and date_from > date_to:
        raise ValueError('La fecha inicial debe ser anterior a la fecha final')
    sql = """SELECT DATE(o.closed_at) report_date,o.id order_id,t.table_number,u.full_name waiter,
             l.name location,o.total,COALESCE(p.method,'Sin pago') payment_method,
             GROUP_CONCAT(CONCAT(pr.name,' x',oi.quantity) ORDER BY pr.name SEPARATOR ', ') products
             FROM orders o JOIN tables_bar t ON t.id=o.table_id
             JOIN users u ON u.id=o.waiter_id JOIN locations l ON l.id=o.location_id
             LEFT JOIN payments p ON p.order_id=o.id
             LEFT JOIN order_items oi ON oi.order_id=o.id
             LEFT JOIN products pr ON pr.id=oi.product_id
             WHERE o.status='Cerrado' AND o.location_id=%s"""
    params = [location_id]
    if date_from:
        sql += ' AND DATE(o.closed_at)>=%s'
        params.append(date_from)
    if date_to:
        sql += ' AND DATE(o.closed_at)<=%s'
        params.append(date_to)
    sql += """ GROUP BY o.id,DATE(o.closed_at),t.table_number,u.full_name,l.name,o.total,p.method
               ORDER BY o.closed_at DESC,o.id DESC"""
    db = connection()
    try:
        cur = db.cursor(dictionary=True)
        cur.execute(sql, tuple(params))
        return cur.fetchall()
    finally:
        db.close()
class APIHandler(BaseHTTPRequestHandler):
    def log_request(self, code='-', size='-'):
        print(f'[API] {self.command} {self.path} -> {code}')

    def send_json(self, data, status=200, cookie=None):
        body = json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')
        self.send_response(status); self.send_header('Content-Type', 'application/json; charset=utf-8'); self.send_header('Content-Length', str(len(body)))
        if cookie: self.send_header('Set-Cookie', cookie)
        self.send_header('Access-Control-Allow-Origin', 'http://127.0.0.1:5000'); self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization'); self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, OPTIONS'); self.end_headers(); self.wfile.write(body)

    def send_file(self, content, filename, content_type):
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_OPTIONS(self): self.send_json({'ok': True})

    def current_user(self):
        token = self.headers.get('Cookie', '').replace('barwise_session=', '').split(';', 1)[0].strip()
        if not token:
            token = self.headers.get('Authorization', '').removeprefix('Bearer ').strip()
        return user_from_session(token) if token else None

    def active_location(self, user):
        """Admin puede cambiar la sede con X-Location-ID; los demas quedan fijos."""
        requested = self.headers.get('X-Location-ID')
        if user['role'] != 'Administrador':
            return user['location_id']
        if requested:
            try:
                requested = int(requested)
            except ValueError:
                return None
            if any(location['id'] == requested and location['active'] for location in LOCATIONS):
                return requested
            return None
        return 1

    def location_user(self):
        user = self.require_user()
        if not user:
            return None, None
        location_id = self.active_location(user)
        if not location_id:
            self.send_json({'error': 'La sede seleccionada no es valida'}, 400)
            return None, None
        return user, location_id

    def require_user(self, roles=None):
        user = self.current_user()
        if not user:
            self.send_json({'error': 'Autenticacion requerida'}, 401); return None
        if roles and user['role'] not in roles:
            self.send_json({'error': 'No tienes permisos para esta operacion'}, 403); return None
        return user

    def do_GET(self):
        global LOCATIONS, TABLES, PRODUCTS, ORDERS
        path = urlparse(self.path).path.rstrip('/') or '/'
        if path == '/api/health':
            try: database = 'connected' if check_connection() else 'not_configured'
            except Exception: database = 'not_configured'
            return self.send_json({'status': 'ok', 'service': 'barwise-backend', 'database': database, 'time': datetime.now().isoformat()})
        if path == '/api/me':
            user = self.require_user()
            if not user: return
            return self.send_json({'user': public_user(user), 'active_location_id': self.active_location(user), 'can_change_location': user['role'] == 'Administrador'})
        if path == '/api/locations':
            user = self.require_user()
            if not user: return
            data = LOCATIONS if user['role'] == 'Administrador' else [location for location in LOCATIONS if location['id'] == user['location_id']]
            return self.send_json({'data': data})
        if path == '/api/algorithms':
            user = self.require_user(['Administrador'])
            if not user: return
            location_id = self.active_location(user)
            if not location_id:
                return self.send_json({'error': 'La sede seleccionada no es valida'}, 400)
            _, _, _, products, orders = load_state(location_id)
            inventory = [{'name': product.get('name'), 'stock': product.get('stock', 0), 'minimum': 5}
                         for product in products]
            sample_items = orders[0].get('items', []) if orders else []
            all_items = [item for order in orders for item in order.get('items', [])]
            return self.send_json({'data': {
                'algorithms': [
                    {'name': 'Binary search', 'complexity': 'O(log n)', 'purpose': 'Find a product by name or code',
                     'result': binary_search_products(products, products[0].get('name')) if products else None},
                    {'name': 'Merge sort', 'complexity': 'O(n log n)', 'purpose': 'Sort products by stock descending',
                     'result': merge_sort_products(products, 'stock', True)},
                    {'name': 'Inventory alerts', 'complexity': 'O(n)', 'purpose': 'Detect low-stock products',
                     'result': inventory_alerts(inventory)},
                    {'name': 'Order total', 'complexity': 'O(n)', 'purpose': 'Calculate item subtotals and order total',
                     'result': calculate_order_total(sample_items)},
                    {'name': 'Sales summary', 'complexity': 'O(n)', 'purpose': 'Group closed sales by date',
                     'result': sales_summary([])},
                    {'name': 'Linear search', 'complexity': 'O(n)', 'purpose': 'Search partial product matches',
                     'result': linear_search_products(products, '')},
                    {'name': 'Quick Sort', 'complexity': 'O(n log n) average', 'purpose': 'Rank active orders by total',
                     'result': quick_sort_orders(orders)},
                    {'name': 'Hash consolidation', 'complexity': 'O(n)', 'purpose': 'Merge repeated order items',
                     'result': consolidate_order_items(all_items)},
                    {'name': 'Pagination', 'complexity': 'O(1) slicing', 'purpose': 'Split catalog results into pages',
                     'result': paginate(products, 1, 10)},
                    {'name': 'Greedy change', 'complexity': 'O(d)', 'purpose': 'Calculate payment change by denominations',
                     'result': calculate_change(10000, 20000)},
                    {'name': 'Inventory projection', 'complexity': 'O(1)', 'purpose': 'Project stock consumption',
                     'result': inventory_projection(products[0].get('stock', 0), 1, 7) if products else None},
                    {'name': 'Top-selling ranking', 'complexity': 'O(n log n)', 'purpose': 'Rank products by quantity sold',
                     'result': top_selling_products(all_items)}
                ],
                'location_id': location_id
            }})
        if path == '/api/bootstrap':
            user = self.require_user()
            if not user: return
            location_id = self.active_location(user)
            if not location_id:
                return self.send_json({'error': 'La sede seleccionada no es valida'}, 400)
            _, LOCATIONS, TABLES, PRODUCTS, ORDERS = load_state(location_id)
            return self.send_json({'user': public_user(user), 'locations': LOCATIONS if user['role'] == 'Administrador' else [location for location in LOCATIONS if location['id'] == user['location_id']], 'tables': [table for table in TABLES if table['location_id'] == location_id], 'products': PRODUCTS, 'orders': [order for order in ORDERS if order.get('location_id', 1) == location_id], 'active_location_id': location_id})
        if path.startswith('/api/locations/') and path.endswith('/tables'):
            user = self.require_user()
            if not user: return
            try: location_id = int(path.split('/')[3])
            except (IndexError, ValueError): return self.send_json({'error': 'Sede invalida'}, 400)
            if not any(location['id'] == location_id for location in LOCATIONS): return self.send_json({'error': 'Sede no encontrada'}, 404)
            if user['role'] != 'Administrador' and user['location_id'] != location_id: return self.send_json({'error': 'No tienes acceso a esta sede'}, 403)
            return self.send_json({'location_id': location_id, 'data': [table for table in TABLES if table['location_id'] == location_id]})
        if path.startswith('/api/orders/'):
            user, location_id = self.location_user()
            if not user: return
            try:
                order_id = int(path.rsplit('/', 1)[1])
            except ValueError:
                return self.send_json({'error': 'Pedido invalido'}, 400)
            db = connection()
            try:
                cur = db.cursor(dictionary=True)
                cur.execute("""SELECT o.id,o.location_id,o.table_id,CONCAT('Mesa ',LPAD(t.table_number,2,'0')) table_name,
                               u.full_name waiter,o.status,o.total,o.opened_at created_at,o.closed_at,
                               p.method,p.paid_at,p.cashier_id,i.invoice_number
                               FROM orders o JOIN tables_bar t ON t.id=o.table_id
                               JOIN users u ON u.id=o.waiter_id
                               LEFT JOIN payments p ON p.order_id=o.id
                               LEFT JOIN invoices i ON i.order_id=o.id
                               WHERE o.id=%s AND o.location_id=%s""", (order_id, location_id))
                order = cur.fetchone()
                if not order:
                    return self.send_json({'error': 'Pedido no encontrado en la sede activa'}, 404)
                cur.execute("""SELECT oi.product_id,p.name,oi.quantity,oi.unit_price price
                               FROM order_items oi JOIN products p ON p.id=oi.product_id
                               WHERE oi.order_id=%s ORDER BY oi.id""", (order_id,))
                order['items'] = cur.fetchall()
                order['created_at'] = order['created_at'].isoformat() if order.get('created_at') else None
                order['closed_at'] = order['closed_at'].isoformat() if order.get('closed_at') else None
                if order.get('paid_at'):
                    order['payment'] = {'method': order.pop('method'), 'paid_at': order.pop('paid_at').isoformat(),
                                        'cashier_id': order.pop('cashier_id')}
                else:
                    order.pop('method', None)
                    order.pop('paid_at', None)
                    order.pop('cashier_id', None)
                return self.send_json({'data': order})
            finally:
                db.close()
        protected = {'/api/tables': TABLES, '/api/products': PRODUCTS, '/api/orders': ORDERS}
        if path in protected:
            user, location_id = self.location_user()
            if not user: return
            data = protected[path]
            if path in ('/api/tables', '/api/orders'):
                _, _, tables, _, orders = load_state(location_id)
                data = tables if path == '/api/tables' else orders
            if path == '/api/products':
                data = load_products(location_id)
            return self.send_json({'location_id': location_id, 'data': data})
        if path == '/api/inventory':
            user, location_id = self.location_user()
            if not user: return
            if user['role'] not in ('Administrador', 'Mesero'):
                return self.send_json({'error': 'No tienes permisos para consultar inventario'}, 403)
            products = load_products(location_id)
            return self.send_json({'location_id': location_id, 'data': [{'product_id': p['id'], 'product': p['name'], 'stock': p['stock']} for p in products]})
        if path in ('/api/reports/sales', '/api/reports/sales.xlsx'):
            user = self.require_user(['Administrador', 'Cajero'])
            if not user: return
            query = parse_qs(urlparse(self.path).query)
            location_id = self.active_location(user)
            if not location_id:
                return self.send_json({'error': 'La sede seleccionada no es valida'}, 400)
            try:
                rows = sales_report(location_id, query.get('from', [''])[0], query.get('to', [''])[0])
            except ValueError as error:
                return self.send_json({'error': str(error)}, 400)
            if path == '/api/reports/sales':
                return self.send_json({'data': rows})
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = 'Ventas'
            sheet.append(['Fecha', 'Pedido', 'Mesa', 'Mesero', 'Sede', 'Total', 'Medio de pago', 'Productos vendidos'])
            for row in rows:
                sheet.append([str(row['report_date']), row['order_id'], row['table_number'], row['waiter'],
                              row['location'], float(row['total']), row['payment_method'], row['products'] or ''])
            sheet.freeze_panes = 'A2'
            sheet.auto_filter.ref = sheet.dimensions
            for column, width in zip('ABCDEFGH', (14, 12, 10, 24, 18, 16, 20, 48)):
                sheet.column_dimensions[column].width = width
            output = BytesIO()
            workbook.save(output)
            return self.send_file(output.getvalue(), 'barwise-reportes.xlsx',
                                  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        if path == '/api/users':
            if not self.require_user(['Administrador']): return
            db = connection()
            try:
                cur = db.cursor(dictionary=True)
                cur.execute("""SELECT u.id,u.username,u.full_name name,r.name role,u.location_id,u.active
                               FROM users u JOIN roles r ON r.id=u.role_id ORDER BY u.id""")
                return self.send_json({'data': cur.fetchall()})
            finally:
                db.close()
        if path.startswith('/api/products/') and path.endswith('/update'):
            admin = self.require_user(['Administrador'])
            if not admin: return
            try:
                product_id = int(path.strip('/').split('/')[2])
                purchase_price = float(data.get('purchase_price'))
                sale_price = float(data.get('price'))
                supplier_id = data.get('supplier_id')
                if supplier_id is not None:
                    supplier_id = int(supplier_id)
            except (IndexError, TypeError, ValueError):
                return self.send_json({'error': 'Los datos del producto no son validos'}, 400)
            code, name = str(data.get('code', '')).strip(), str(data.get('name', '')).strip()
            category_name = data.get('category')
            active = data.get('active')
            if not code or not name or purchase_price < 0 or sale_price <= 0 or not isinstance(active, bool):
                return self.send_json({'error': 'Codigo, nombre, precios y estado son obligatorios'}, 400)
            db = connection()
            try:
                cur = db.cursor()
                cur.execute('SELECT id FROM categories WHERE name=%s AND active=TRUE', (category_name,))
                category = cur.fetchone()
                if not category:
                    return self.send_json({'error': 'Categoria invalida o inactiva'}, 400)
                if supplier_id is not None:
                    cur.execute('SELECT id FROM suppliers WHERE id=%s AND active=TRUE', (supplier_id,))
                    if not cur.fetchone():
                        return self.send_json({'error': 'El proveedor seleccionado no existe o esta inactivo'}, 400)
                cur.execute('UPDATE products SET code=%s,name=%s,category_id=%s,purchase_price=%s,sale_price=%s,active=%s WHERE id=%s',
                            (code, name, category[0], purchase_price, sale_price, active, product_id))
                if cur.rowcount != 1:
                    db.rollback()
                    return self.send_json({'error': 'Producto no encontrado'}, 404)
                cur.execute('DELETE FROM supplier_products WHERE product_id=%s', (product_id,))
                if supplier_id is not None:
                    cur.execute('INSERT INTO supplier_products(supplier_id,product_id,last_purchase_price) VALUES(%s,%s,%s)',
                                (supplier_id, product_id, purchase_price))
                audit(cur, admin['id'], 'Actualizar producto', 'products', product_id,
                      {'category': category_name, 'supplier_id': supplier_id, 'active': active})
                db.commit()
                return self.send_json({'id': product_id, 'message': 'Producto actualizado'})
            except mysql.connector.IntegrityError:
                db.rollback()
                return self.send_json({'error': 'El codigo del producto ya esta registrado'}, 409)
            except mysql.connector.Error as error:
                db.rollback()
                print(f'[API] No fue posible actualizar el producto: {error}')
                return self.send_json({'error': 'No fue posible actualizar el producto'}, 500)
            finally:
                db.close()
        if path == '/api/suppliers':
            if not self.require_user(['Administrador']): return
            return self.send_json({'data': load_suppliers()})
        if path == '/api/categories':
            if not self.require_user(['Administrador']): return
            db = connection()
            try:
                cur = db.cursor(dictionary=True)
                cur.execute('SELECT id,name,active FROM categories ORDER BY name')
                return self.send_json({'data': cur.fetchall()})
            finally:
                db.close()
        if path == '/api/payment-methods':
            user = self.require_user(['Administrador', 'Cajero'])
            if not user: return
            db = connection()
            try:
                cur = db.cursor(dictionary=True)
                cur.execute('SELECT id,name,active FROM payment_methods ORDER BY id')
                return self.send_json({'data': cur.fetchall()})
            finally:
                db.close()
        self.send_json({'error': 'Ruta no encontrada'}, 404)

    def do_POST(self):
        path = urlparse(self.path).path.rstrip('/') or '/'
        try: data = json_body(self)
        except ValueError as error: return self.send_json({'error': str(error)}, 400)
        if path == '/api/auth/login':
            result = login(str(data.get('username', '')), str(data.get('password', '')))
            if not result: return self.send_json({'error': 'Usuario o contrasena incorrectos'}, 401)
            token, user = result
            return self.send_json({'user': public_user(user), 'message': 'Login correcto'}, cookie=f'barwise_session={token}; HttpOnly; SameSite=Lax; Path=/')
        if path == '/api/auth/logout':
            logout(self.headers.get('Cookie', '').replace('barwise_session=', '').split(';', 1)[0].strip()); return self.send_json({'message': 'Sesion cerrada'})
        if path == '/api/locations':
            admin = self.require_user(['Administrador'])
            if not admin: return
            name, address = str(data.get('name', '')).strip(), str(data.get('address', '')).strip()
            if not name or not address:
                return self.send_json({'error': 'Nombre y direccion son obligatorios'}, 400)
            db = connection()
            try:
                cur = db.cursor()
                cur.execute('INSERT INTO locations(name,address,active) VALUES(%s,%s,TRUE)', (name, address))
                location_id = cur.lastrowid
                audit(cur, admin['id'], 'Crear sede', 'locations', location_id, {'name': name})
                db.commit()
                return self.send_json({'id': location_id, 'name': name, 'address': address}, 201)
            except mysql.connector.IntegrityError:
                db.rollback()
                return self.send_json({'error': 'Ya existe una sede con ese nombre'}, 409)
            except mysql.connector.Error as error:
                db.rollback()
                print(f'[API] No fue posible registrar la sede: {error}')
                return self.send_json({'error': 'No fue posible registrar la sede'}, 500)
            finally:
                db.close()
        if path.startswith('/api/locations/') and path.endswith('/update'):
            admin = self.require_user(['Administrador'])
            if not admin: return
            try:
                location_id = int(path.strip('/').split('/')[2])
            except (IndexError, ValueError):
                return self.send_json({'error': 'Sede invalida'}, 400)
            name, address = str(data.get('name', '')).strip(), str(data.get('address', '')).strip()
            if not name or not address or len(name) > 80 or len(address) > 180:
                return self.send_json({'error': 'Nombre y direccion son obligatorios y deben tener una longitud valida'}, 400)
            db = connection()
            try:
                cur = db.cursor()
                cur.execute('SELECT id FROM locations WHERE id=%s', (location_id,))
                if not cur.fetchone():
                    db.rollback()
                    return self.send_json({'error': 'Sede no encontrada'}, 404)
                cur.execute('UPDATE locations SET name=%s,address=%s WHERE id=%s', (name, address, location_id))
                audit(cur, admin['id'], 'Actualizar sede', 'locations', location_id, {'name': name, 'address': address})
                db.commit()
                return self.send_json({'id': location_id, 'name': name, 'address': address})
            except mysql.connector.IntegrityError:
                db.rollback()
                return self.send_json({'error': 'Ya existe una sede con ese nombre'}, 409)
            except mysql.connector.Error as error:
                db.rollback()
                print(f'[API] No fue posible actualizar la sede: {error}')
                return self.send_json({'error': 'No fue posible actualizar la sede'}, 500)
            finally:
                db.close()
        if path == '/api/tables':
            admin = self.require_user(['Administrador'])
            if not admin: return
            location_id, table_number = data.get('location_id'), data.get('table_number')
            seats = data.get('seats', 4)
            if (isinstance(location_id, bool) or not isinstance(location_id, int)
                    or isinstance(table_number, bool) or not isinstance(table_number, int) or table_number < 1
                    or isinstance(seats, bool) or not isinstance(seats, int) or not 1 <= seats <= 30
                    or not any(location['id'] == location_id and location['active'] for location in LOCATIONS)):
                return self.send_json({'error': 'Sede, numero de mesa o puestos invalidos'}, 400)
            db = connection()
            try:
                cur = db.cursor()
                cur.execute("INSERT INTO tables_bar(location_id,table_number,seats,status) VALUES(%s,%s,%s,'Libre')",
                            (location_id, table_number, seats))
                table_id = cur.lastrowid
                audit(cur, admin['id'], 'Crear mesa', 'tables_bar', table_id, {'location_id': location_id, 'table_number': table_number})
                db.commit()
                return self.send_json({'id': table_id, 'location_id': location_id, 'table_number': table_number, 'seats': seats, 'status': 'Libre'}, 201)
            except mysql.connector.IntegrityError:
                db.rollback()
                return self.send_json({'error': 'Ya existe ese numero de mesa en la sede'}, 409)
            except mysql.connector.Error as error:
                db.rollback()
                print(f'[API] No fue posible registrar la mesa: {error}')
                return self.send_json({'error': 'No fue posible registrar la mesa'}, 500)
            finally:
                db.close()
        if path in ('/api/categories', '/api/payment-methods'):
            admin = self.require_user(['Administrador'])
            if not admin: return
            table = 'categories' if path == '/api/categories' else 'payment_methods'
            value = str(data.get('name', '')).strip()
            if not value:
                return self.send_json({'error': 'El nombre es obligatorio'}, 400)
            if table == 'payment_methods' and value not in ('Efectivo', 'Credito', 'Debito'):
                return self.send_json({'error': 'El medio de pago no esta contemplado'}, 400)
            db = connection()
            try:
                cur = db.cursor()
                cur.execute(f'INSERT INTO {table}(name,active) VALUES(%s,TRUE)', (value,))
                record_id = cur.lastrowid
                audit(cur, admin['id'], 'Crear parametrizacion', table, record_id, {'name': value})
                db.commit()
                return self.send_json({'id': record_id, 'name': value, 'active': True}, 201)
            except mysql.connector.IntegrityError:
                db.rollback()
                return self.send_json({'error': 'Ese nombre ya esta registrado'}, 409)
            except mysql.connector.Error as error:
                db.rollback()
                print(f'[API] No fue posible guardar la parametrizacion: {error}')
                return self.send_json({'error': 'No fue posible guardar la parametrizacion'}, 500)
            finally:
                db.close()
        if path.startswith(('/api/users/', '/api/products/', '/api/suppliers/', '/api/categories/', '/api/payment-methods/')) and path.endswith('/status'):
            admin = self.require_user(['Administrador'])
            if not admin: return
            parts = path.strip('/').split('/')
            try:
                record_id = int(parts[2])
            except (IndexError, ValueError):
                return self.send_json({'error': 'Registro invalido'}, 400)
            active = data.get('active')
            if not isinstance(active, bool):
                return self.send_json({'error': 'El estado debe ser verdadero o falso'}, 400)
            table_name = {'users': 'users', 'products': 'products', 'suppliers': 'suppliers',
                          'categories': 'categories', 'payment-methods': 'payment_methods'}.get(parts[1])
            if not table_name:
                return self.send_json({'error': 'Ruta no encontrada'}, 404)
            db = connection()
            try:
                cur = db.cursor()
                cur.execute(f'UPDATE {table_name} SET active=%s WHERE id=%s', (active, record_id))
                if cur.rowcount != 1:
                    db.rollback()
                    return self.send_json({'error': 'Registro no encontrado'}, 404)
                if parts[1] == 'users' and not active:
                    cur.execute('DELETE FROM sessions WHERE user_id=%s', (record_id,))
                audit(cur, admin['id'], 'Cambiar estado', table_name, record_id, {'active': active})
                db.commit()
                return self.send_json({'id': record_id, 'active': active})
            except mysql.connector.Error as error:
                db.rollback()
                print(f'[API] No fue posible cambiar el estado: {error}')
                return self.send_json({'error': 'No fue posible cambiar el estado'}, 500)
            finally:
                db.close()
        if path.startswith('/api/users/') and path.endswith('/update'):
            admin = self.require_user(['Administrador'])
            if not admin: return
            try:
                target_id = int(path.strip('/').split('/')[2])
            except (IndexError, ValueError):
                return self.send_json({'error': 'Usuario invalido'}, 400)
            role = str(data.get('role', '')).strip()
            full_name = str(data.get('name', '')).strip()
            password = str(data.get('password', ''))
            location_id = data.get('location_id')
            if role not in ('Administrador', 'Cajero', 'Mesero') or not full_name or len(full_name) > 120:
                return self.send_json({'error': 'Nombre y perfil validos son obligatorios'}, 400)
            if password and len(password) < 8:
                return self.send_json({'error': 'La nueva contraseña debe tener al menos 8 caracteres'}, 400)
            if role == 'Administrador':
                location_id = None
            else:
                if isinstance(location_id, bool):
                    return self.send_json({'error': 'Seleccione una sede activa para este perfil'}, 400)
                try:
                    location_id = int(location_id)
                except (TypeError, ValueError):
                    return self.send_json({'error': 'Seleccione una sede activa para este perfil'}, 400)
            if target_id == admin['id'] and (role != admin['role'] or location_id != admin.get('location_id')):
                return self.send_json({'error': 'No puedes cambiar tu propio perfil o sede mientras la sesion esta activa'}, 409)
            db = connection()
            try:
                cur = db.cursor(dictionary=True)
                cur.execute('SELECT id,username FROM users WHERE id=%s', (target_id,))
                target = cur.fetchone()
                if not target:
                    db.rollback()
                    return self.send_json({'error': 'Usuario no encontrado'}, 404)
                if location_id is not None:
                    cur.execute('SELECT id FROM locations WHERE id=%s AND active=TRUE', (location_id,))
                    if not cur.fetchone():
                        db.rollback()
                        return self.send_json({'error': 'La sede seleccionada no existe o esta inactiva'}, 400)
                cur.execute('SELECT id FROM roles WHERE name=%s', (role,))
                role_row = cur.fetchone()
                if not role_row:
                    db.rollback()
                    return self.send_json({'error': 'El perfil seleccionado no existe'}, 400)
                if password:
                    cur.execute('UPDATE users SET full_name=%s,role_id=%s,location_id=%s,password_hash=%s WHERE id=%s',
                                (full_name, role_row['id'], location_id, password_hash(password), target_id))
                else:
                    cur.execute('UPDATE users SET full_name=%s,role_id=%s,location_id=%s WHERE id=%s',
                                (full_name, role_row['id'], location_id, target_id))
                current_token = self.headers.get('Cookie', '').replace('barwise_session=', '').split(';', 1)[0].strip()
                if target_id == admin['id'] and current_token:
                    current_token_hash = hashlib.sha256(current_token.encode('utf-8')).hexdigest()
                    cur.execute('DELETE FROM sessions WHERE user_id=%s AND token<>%s',
                                (target_id, current_token_hash))
                else:
                    cur.execute('DELETE FROM sessions WHERE user_id=%s', (target_id,))
                audit(cur, admin['id'], 'Actualizar usuario', 'users', target_id,
                      {'name': full_name, 'role': role, 'location_id': location_id,
                       'password_changed': bool(password)})
                db.commit()
            except mysql.connector.Error as error:
                db.rollback()
                print(f'[API] No fue posible actualizar el usuario: {error}')
                return self.send_json({'error': 'No fue posible actualizar el usuario'}, 500)
            finally:
                db.close()
            updated_user = USERS.get(target['username'])
            if updated_user:
                updated_user.update({'name': full_name, 'role': role, 'location_id': location_id})
                if password:
                    updated_user['password'] = password_hash(password)
            return self.send_json({'id': target_id, 'name': full_name, 'role': role,
                                   'location_id': location_id})
        if path == '/api/users':
            admin = self.require_user(['Administrador'])
            if not admin: return
            username = str(data.get('username', '')).lower()
            full_name = str(data.get('name', '')).strip()
            password = str(data.get('password', ''))
            if not username or not full_name or len(password) < 8:
                return self.send_json({'error': 'Usuario, nombre y contraseña de al menos 8 caracteres son obligatorios'}, 400)
            role = data.get('role', 'Mesero')
            location_id = data.get('location_id') if role in ('Cajero', 'Mesero') else None
            if role != 'Administrador' and isinstance(location_id, bool):
                return self.send_json({'error': 'Seleccione una sede para este perfil'}, 400)
            if role not in ('Administrador', 'Cajero', 'Mesero') or (role != 'Administrador' and not any(location['id'] == location_id for location in LOCATIONS)):
                return self.send_json({'error': 'El rol o la sede del usuario no son validos'}, 400)
            db = connection()
            try:
                cur = db.cursor()
                if location_id is not None:
                    cur.execute('SELECT id FROM locations WHERE id=%s AND active=TRUE', (location_id,))
                    if not cur.fetchone():
                        db.rollback()
                        return self.send_json({'error': 'La sede seleccionada no existe o esta inactiva'}, 400)
                cur.execute('SELECT id FROM roles WHERE name=%s', (role,))
                role_row = cur.fetchone()
                cur.execute('INSERT INTO users(username,full_name,password_hash,role_id,location_id,active) VALUES(%s,%s,%s,%s,%s,TRUE)',
                            (username, full_name, password_hash(password), role_row[0], location_id))
                user_id = cur.lastrowid
                audit(cur, admin['id'], 'Crear usuario', 'users', user_id, {'username': username, 'role': role, 'location_id': location_id})
                db.commit()
            except mysql.connector.IntegrityError:
                db.rollback()
                return self.send_json({'error': 'El nombre de usuario ya esta registrado'}, 409)
            except mysql.connector.Error as error:
                db.rollback()
                print(f'[API] No fue posible registrar el usuario: {error}')
                return self.send_json({'error': 'No fue posible registrar el usuario'}, 500)
            finally:
                db.close()
            created_user = {'id': user_id, 'username': username, 'name': full_name, 'role': role,
                            'location_id': location_id, 'active': True, 'password': password_hash(password)}
            USERS[username] = created_user
            return self.send_json({'user': public_user(created_user)}, 201)
        if path == '/api/products':
            admin = self.require_user(['Administrador'])
            if not admin: return
            location_id = self.active_location(admin)
            if not location_id:
                return self.send_json({'error': 'La sede seleccionada no es valida'}, 400)
            code, name = str(data.get('code', '')).strip(), str(data.get('name', '')).strip()
            supplier_id = data.get('supplier_id')
            try:
                purchase_price = float(data.get('purchase_price', 0))
                sale_price = float(data.get('price', 0))
            except (TypeError, ValueError):
                return self.send_json({'error': 'Los valores de compra y venta deben ser numericos'}, 400)
            if not code or not name or purchase_price < 0 or sale_price <= 0:
                return self.send_json({'error': 'Codigo, nombre, compra valida y venta mayor que cero son obligatorios'}, 400)
            db = connection()
            try:
                cur = db.cursor()
                cur.execute('SELECT id FROM categories WHERE name=%s', (data.get('category', 'Licores'),))
                category = cur.fetchone()
                if not category: return self.send_json({'error': 'Categoria invalida'}, 400)
                if supplier_id is not None:
                    cur.execute('SELECT id FROM suppliers WHERE id=%s AND active=TRUE', (supplier_id,))
                    if not cur.fetchone():
                        return self.send_json({'error': 'El proveedor seleccionado no existe o esta inactivo'}, 400)
                cur.execute('INSERT INTO products(code,name,category_id,purchase_price,sale_price,active) VALUES(%s,%s,%s,%s,%s,%s)',
                            (code, name, category[0], purchase_price, sale_price, bool(data.get('active', True))))
                product_id = cur.lastrowid
                cur.execute('INSERT INTO inventory(location_id,product_id,quantity,minimum_quantity) VALUES(%s,%s,0,0)',
                            (location_id, product_id))
                if supplier_id is not None:
                    cur.execute('INSERT INTO supplier_products(supplier_id,product_id,last_purchase_price) VALUES(%s,%s,%s)',
                                (supplier_id, product_id, purchase_price))
                audit(cur, admin['id'], 'Crear producto', 'products', product_id,
                      {'code': code, 'location_id': location_id, 'supplier_id': supplier_id})
                db.commit()
                return self.send_json({'message': 'Producto registrado', 'id': product_id}, 201)
            except mysql.connector.IntegrityError:
                db.rollback()
                return self.send_json({'error': 'El codigo del producto ya esta registrado'}, 409)
            except mysql.connector.Error as error:
                db.rollback()
                print(f'[API] No fue posible registrar el producto: {error}')
                return self.send_json({'error': 'No fue posible registrar el producto'}, 500)
            finally:
                db.close()
        if path == '/api/suppliers':
            admin = self.require_user(['Administrador'])
            if not admin: return
            fields = {key: str(data.get(key, '')).strip() for key in ('name', 'identification', 'country', 'city', 'phone')}
            if not all(fields.values()):
                return self.send_json({'error': 'Todos los datos del proveedor son obligatorios'}, 400)
            db = connection()
            try:
                cur = db.cursor()
                cur.execute('INSERT INTO suppliers(identification,name,country,city,phone,active) VALUES(%s,%s,%s,%s,%s,TRUE)', (fields['identification'], fields['name'], fields['country'], fields['city'], fields['phone']))
                supplier_id = cur.lastrowid
                audit(cur, admin['id'], 'Crear proveedor', 'suppliers', supplier_id, {'identification': fields['identification']})
                db.commit()
                return self.send_json({'message': 'Proveedor registrado', 'id': supplier_id}, 201)
            except mysql.connector.IntegrityError:
                db.rollback()
                return self.send_json({'error': 'La identificación ya está registrada'}, 409)
            except mysql.connector.Error as error:
                db.rollback()
                print(f'[API] No fue posible registrar el proveedor: {error}')
                return self.send_json({'error': 'No fue posible registrar el proveedor'}, 500)
            finally:
                db.close()
        if path.startswith('/api/suppliers/') and path.endswith('/update'):
            admin = self.require_user(['Administrador'])
            if not admin: return
            try:
                supplier_id = int(path.strip('/').split('/')[2])
            except (IndexError, ValueError):
                return self.send_json({'error': 'Proveedor invalido'}, 400)
            fields = {key: str(data.get(key, '')).strip() for key in ('name', 'identification', 'country', 'city', 'phone')}
            max_lengths = {'name': 140, 'identification': 40, 'country': 80, 'city': 80, 'phone': 40}
            if not all(fields.values()) or any(len(fields[key]) > limit for key, limit in max_lengths.items()):
                return self.send_json({'error': 'Los datos del proveedor son obligatorios y deben tener una longitud valida'}, 400)
            db = connection()
            try:
                cur = db.cursor()
                cur.execute('SELECT id FROM suppliers WHERE id=%s', (supplier_id,))
                if not cur.fetchone():
                    db.rollback()
                    return self.send_json({'error': 'Proveedor no encontrado'}, 404)
                cur.execute('UPDATE suppliers SET identification=%s,name=%s,country=%s,city=%s,phone=%s WHERE id=%s',
                            (fields['identification'], fields['name'], fields['country'], fields['city'], fields['phone'], supplier_id))
                audit(cur, admin['id'], 'Actualizar proveedor', 'suppliers', supplier_id,
                      {'identification': fields['identification']})
                db.commit()
                return self.send_json({'id': supplier_id, 'message': 'Proveedor actualizado'})
            except mysql.connector.IntegrityError:
                db.rollback()
                return self.send_json({'error': 'La identificación ya está registrada'}, 409)
            except mysql.connector.Error as error:
                db.rollback()
                print(f'[API] No fue posible actualizar el proveedor: {error}')
                return self.send_json({'error': 'No fue posible actualizar el proveedor'}, 500)
            finally:
                db.close()
        if path.startswith('/api/orders/') and path.endswith('/items'):
            order_editor = self.require_user()
            if not order_editor: return
            try:
                order_id = int(path.strip('/').split('/')[2])
            except (IndexError, ValueError):
                return self.send_json({'error': 'Pedido invalido'}, 400)
            location_id = self.active_location(order_editor)
            raw_items = data.get('items')
            replace_mode = data.get('replace') is True
            if not location_id or not isinstance(raw_items, list) or (not raw_items and not replace_mode):
                return self.send_json({'error': 'Selecciona al menos un producto para el pedido'}, 400)
            if replace_mode:
                desired = {}
                for raw in raw_items:
                    if not isinstance(raw, dict) or isinstance(raw.get('product_id'), bool) or not isinstance(raw.get('product_id'), int):
                        return self.send_json({'error': 'El detalle del pedido no es valido'}, 400)
                    quantity = raw.get('quantity')
                    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 0:
                        return self.send_json({'error': 'Las cantidades deben ser mayores o iguales a cero'}, 400)
                    desired[raw['product_id']] = quantity
                db = connection()
                try:
                    cur = db.cursor(dictionary=True)
                    cur.execute('SELECT table_id,status FROM orders WHERE id=%s AND location_id=%s FOR UPDATE', (order_id, location_id))
                    order = cur.fetchone()
                    if not order or order['status'] != 'Abierto':
                        return self.send_json({'error': 'El pedido no existe o no está abierto'}, 409)
                    cur.execute('SELECT product_id,SUM(quantity) quantity,MAX(unit_price) price FROM order_items WHERE order_id=%s GROUP BY product_id', (order_id,))
                    current = {row['product_id']: float(row['quantity']) for row in cur.fetchall()}
                    product_ids = set(current) | set(desired)
                    final_items = []
                    new_total = 0
                    for product_id in sorted(product_ids):
                        wanted = desired.get(product_id, 0)
                        cur.execute('SELECT name,sale_price FROM products WHERE id=%s AND active=TRUE', (product_id,))
                        product = cur.fetchone()
                        if wanted > 0 and not product:
                            return self.send_json({'error': 'El producto no existe o está inactivo'}, 409)
                        cur.execute('SELECT quantity FROM inventory WHERE location_id=%s AND product_id=%s FOR UPDATE', (location_id, product_id))
                        stock_row = cur.fetchone()
                        stock = float(stock_row['quantity']) if stock_row else 0
                        delta = wanted - current.get(product_id, 0)
                        if delta > 0 and stock < delta:
                            return self.send_json({'error': 'Existencia insuficiente para modificar el pedido'}, 409)
                        if delta:
                            cur.execute('UPDATE inventory SET quantity=quantity-%s WHERE location_id=%s AND product_id=%s', (delta, location_id, product_id))
                            movement = 'Salida' if delta > 0 else 'Entrada'
                            cur.execute('INSERT INTO inventory_movements(location_id,product_id,user_id,type,quantity,note) VALUES(%s,%s,%s,%s,%s,%s)', (location_id, product_id, order_editor['id'], movement, abs(delta), f'Edición del pedido {order_id}'))
                        if wanted > 0:
                            price = float(product['sale_price'])
                            final_items.append({'product_id': product_id, 'name': product['name'], 'quantity': wanted, 'price': price})
                            new_total += price * wanted
                    cur.execute('DELETE FROM order_items WHERE order_id=%s', (order_id,))
                    for item in final_items:
                        cur.execute('INSERT INTO order_items(order_id,product_id,quantity,unit_price) VALUES(%s,%s,%s,%s)', (order_id, item['product_id'], item['quantity'], item['price']))
                    cur.execute('UPDATE orders SET total=%s WHERE id=%s', (new_total, order_id))
                    audit(cur, order_editor['id'], 'Editar pedido', 'orders', order_id, {'items': final_items, 'total': new_total})
                    db.commit()
                    cached_order = next((item for item in ORDERS if item['id'] == order_id), None)
                    if cached_order:
                        cached_order['items'], cached_order['total'] = final_items, new_total
                    return self.send_json({'data': {'id': order_id, 'status': 'Abierto', 'items_added': final_items, 'total': new_total}})
                except mysql.connector.Error:
                    db.rollback()
                    return self.send_json({'error': 'No fue posible modificar el pedido'}, 500)
                finally:
                    db.close()
            quantities = {}
            for raw in raw_items:
                if not isinstance(raw, dict):
                    return self.send_json({'error': 'El detalle del pedido no es valido'}, 400)
                product_id, quantity = raw.get('product_id'), raw.get('quantity')
                if (isinstance(product_id, bool) or not isinstance(product_id, int) or product_id < 1
                        or isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1):
                    return self.send_json({'error': 'Los productos y cantidades deben ser validos'}, 400)
                quantities[product_id] = quantities.get(product_id, 0) + quantity
            added_items, added_total = [], 0
            db = connection()
            try:
                cur = db.cursor()
                cur.execute('SELECT table_id,waiter_id,status,total FROM orders WHERE id=%s AND location_id=%s FOR UPDATE',
                            (order_id, location_id))
                order = cur.fetchone()
                if not order:
                    db.rollback()
                    return self.send_json({'error': 'Pedido no encontrado en la sede activa'}, 404)
                if order[2] != 'Abierto':
                    db.rollback()
                    return self.send_json({'error': 'Solo se pueden agregar productos a pedidos abiertos'}, 409)
                for product_id, quantity in sorted(quantities.items()):
                    cur.execute('SELECT name,sale_price FROM products WHERE id=%s AND active=TRUE', (product_id,))
                    product = cur.fetchone()
                    cur.execute('SELECT quantity FROM inventory WHERE location_id=%s AND product_id=%s FOR UPDATE',
                                (location_id, product_id))
                    stock = cur.fetchone()
                    if not product or not stock or float(stock[0]) < quantity:
                        db.rollback()
                        return self.send_json({'error': 'Producto inactivo o existencia insuficiente en la sede'}, 409)
                    item_total = float(product[1]) * quantity
                    added_items.append({'product_id': product_id, 'name': product[0],
                                        'quantity': quantity, 'price': float(product[1])})
                    added_total += item_total
                for item in added_items:
                    cur.execute('INSERT INTO order_items(order_id,product_id,quantity,unit_price) VALUES(%s,%s,%s,%s)',
                                (order_id, item['product_id'], item['quantity'], item['price']))
                    cur.execute('UPDATE inventory SET quantity=quantity-%s WHERE location_id=%s AND product_id=%s',
                                (item['quantity'], location_id, item['product_id']))
                    cur.execute('INSERT INTO inventory_movements(location_id,product_id,user_id,type,quantity,note) VALUES(%s,%s,%s,%s,%s,%s)',
                                (location_id, item['product_id'], order_editor['id'], 'Salida', item['quantity'],
                                 f'Productos agregados al pedido {order_id}'))
                new_total = float(order[3]) + added_total
                cur.execute('UPDATE orders SET total=%s WHERE id=%s', (new_total, order_id))
                audit(cur, order_editor['id'], 'Agregar productos al pedido', 'orders', order_id,
                      {'location_id': location_id, 'items': added_items, 'added_total': added_total,
                       'total': new_total})
                db.commit()
            except mysql.connector.Error as error:
                db.rollback()
                print(f'[API] No fue posible agregar productos al pedido: {error}')
                return self.send_json({'error': 'No fue posible agregar productos al pedido'}, 500)
            finally:
                db.close()
            cached_order = next((item for item in ORDERS if item['id'] == order_id), None)
            if cached_order:
                cached_order['items'].extend(added_items)
                cached_order['total'] = new_total
            return self.send_json({'data': {'id': order_id, 'status': 'Abierto',
                                            'items_added': added_items, 'total': new_total}})
        if path == '/api/orders':
            user = self.require_user()
            if not user: return
            location_id = self.active_location(user)
            if not location_id:
                return self.send_json({'error': 'La sede del usuario no es valida'}, 400)
            table_id = data.get('table_id')
            raw_items = data.get('items')
            if isinstance(table_id, bool) or not isinstance(table_id, int) or not isinstance(raw_items, list) or not raw_items:
                return self.send_json({'error': 'Selecciona una mesa y al menos un producto'}, 400)
            quantities = {}
            for raw in raw_items:
                if not isinstance(raw, dict):
                    return self.send_json({'error': 'El detalle del pedido no es valido'}, 400)
                product_id, quantity = raw.get('product_id'), raw.get('quantity')
                if (isinstance(product_id, bool) or not isinstance(product_id, int) or product_id < 1
                        or isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1):
                    return self.send_json({'error': 'Los productos y cantidades deben ser validos'}, 400)
                quantities[product_id] = quantities.get(product_id, 0) + quantity
            items, total = [], 0
            db = connection()
            try:
                cur = db.cursor()
                cur.execute('SELECT table_number,status FROM tables_bar WHERE id=%s AND location_id=%s FOR UPDATE',
                            (table_id, location_id))
                table = cur.fetchone()
                if not table or table[1] != 'Libre':
                    db.rollback()
                    return self.send_json({'error': 'La mesa no esta disponible'}, 409)
                for product_id, quantity in sorted(quantities.items()):
                    cur.execute('SELECT name,sale_price FROM products WHERE id=%s AND active=TRUE', (product_id,))
                    product = cur.fetchone()
                    cur.execute('SELECT quantity FROM inventory WHERE location_id=%s AND product_id=%s FOR UPDATE',
                                (location_id, product_id))
                    stock = cur.fetchone()
                    if not product or not stock or float(stock[0]) < quantity:
                        db.rollback()
                        return self.send_json({'error': 'Producto inactivo o existencia insuficiente en la sede'}, 409)
                    items.append({'product_id': product_id, 'name': product[0], 'quantity': quantity, 'price': float(product[1])})
                    total += float(product[1]) * quantity
                cur.execute('INSERT INTO orders(location_id,table_id,waiter_id,status,total) VALUES(%s,%s,%s,%s,%s)',
                            (location_id, table_id, user['id'], 'Abierto', total))
                order_id = cur.lastrowid
                for item in items:
                    cur.execute('INSERT INTO order_items(order_id,product_id,quantity,unit_price) VALUES(%s,%s,%s,%s)',
                                (order_id, item['product_id'], item['quantity'], item['price']))
                    cur.execute('UPDATE inventory SET quantity=quantity-%s WHERE location_id=%s AND product_id=%s',
                                (item['quantity'], location_id, item['product_id']))
                    cur.execute('INSERT INTO inventory_movements(location_id,product_id,user_id,type,quantity,note) VALUES(%s,%s,%s,%s,%s,%s)',
                                (location_id, item['product_id'], user['id'], 'Salida', item['quantity'], f'Pedido {order_id}'))
                cur.execute("UPDATE tables_bar SET status='Ocupada' WHERE id=%s", (table_id,))
                audit(cur, user['id'], 'Crear pedido', 'orders', order_id,
                      {'location_id': location_id, 'table_id': table_id, 'items': items, 'total': total})
                db.commit()
            except mysql.connector.Error as error:
                db.rollback()
                print(f'[API] No fue posible registrar el pedido: {error}')
                return self.send_json({'error': 'No fue posible registrar el pedido'}, 500)
            finally:
                db.close()
            order = {'id': order_id, 'location_id': location_id, 'table_id': table_id,
                     'table_name': f'Mesa {int(table[0]):02d}', 'waiter': user['name'], 'status': 'Abierto',
                     'payment': None, 'items': items, 'total': total, 'created_at': datetime.now().isoformat()}
            ORDERS.append(order)
            return self.send_json({'data': order}, 201)
        if path == '/api/payments':
            cashier = self.require_user(['Cajero', 'Administrador'])
            if not cashier: return
            location_id = self.active_location(cashier)
            order_id, method = data.get('order_id'), data.get('method')
            if not location_id or isinstance(order_id, bool) or not isinstance(order_id, int) or method not in ('Efectivo', 'Credito', 'Debito'):
                return self.send_json({'error': 'Pedido, sede o medio de pago invalido'}, 400)
            db = connection()
            try:
                cur = db.cursor()
                cur.execute("SELECT table_id,total,status FROM orders WHERE id=%s AND location_id=%s FOR UPDATE", (order_id, location_id))
                row = cur.fetchone()
                if not row or row[2] != 'Abierto':
                    db.rollback()
                    return self.send_json({'error': 'El pedido no existe o ya no esta abierto'}, 409)
                cur.execute('SELECT id FROM payment_methods WHERE name=%s AND active=TRUE', (method,))
                if not cur.fetchone():
                    db.rollback()
                    return self.send_json({'error': 'El medio de pago no existe o esta inactivo'}, 400)
                cur.execute('INSERT INTO payments(order_id,cashier_id,method,amount) VALUES(%s,%s,%s,%s)',
                            (order_id, cashier['id'], method, row[1]))
                table_id, total = row[0], row[1]
                cur.execute("UPDATE orders SET status='Cerrado',closed_at=NOW() WHERE id=%s", (order_id,))
                cur.execute("UPDATE tables_bar SET status='Libre' WHERE id=%s AND location_id=%s AND status='Ocupada'",
                            (table_id, location_id))
                if cur.rowcount != 1:
                    db.rollback()
                    return self.send_json({'error': 'No fue posible liberar la mesa del pedido'}, 409)
                invoice_number = f'FV-{order_id:07d}'
                cur.execute('INSERT INTO invoices(order_id,invoice_number) VALUES(%s,%s)',
                            (order_id, invoice_number))
                audit(cur, cashier['id'], 'Registrar pago y cerrar pedido', 'orders', order_id,
                      {'location_id': location_id, 'table_id': table_id, 'method': method,
                       'amount': float(total), 'invoice': invoice_number})
                db.commit()
            except mysql.connector.IntegrityError:
                db.rollback()
                return self.send_json({'error': 'El pedido ya fue pagado, cerrado o facturado'}, 409)
            except mysql.connector.Error as error:
                db.rollback()
                print(f'[API] No fue posible registrar el pago: {error}')
                return self.send_json({'error': 'No fue posible registrar el pago'}, 500)
            finally:
                db.close()
            closed_at = datetime.now().isoformat()
            for order in ORDERS:
                if order['id'] == order_id:
                    order['status'] = 'Cerrado'
                    order['closed_at'] = closed_at
                    order['invoice_number'] = invoice_number
                    order['method'] = method
                    order['payment'] = {'method': method, 'paid_at': closed_at,
                                        'cashier_id': cashier['id']}
                    break
            for table in TABLES:
                if table['id'] == table_id:
                    table['status'], table['order_id'] = 'Libre', None
                    break
            return self.send_json({
                'data': next((order for order in ORDERS if order['id'] == order_id),
                             {'id': order_id, 'status': 'Cerrado', 'total': float(total),
                              'payment': {'method': method}}),
                'invoice': {'number': invoice_number, 'order_id': order_id},
                'table': {'id': table_id, 'status': 'Libre'},
            })
        if path == '/api/inventory/movements':
            user, location_id = self.location_user()
            if not user or user['role'] != 'Administrador': return
            product_id, movement = data.get('product_id'), data.get('type')
            quantity, note = data.get('quantity'), str(data.get('note', '')).strip()
            if (isinstance(product_id, bool) or not isinstance(product_id, int)
                    or isinstance(quantity, bool) or not isinstance(quantity, int)
                    or quantity <= 0 or movement not in ('Entrada', 'Salida')):
                return self.send_json({'error': 'Movimiento invalido'}, 400)
            db = connection()
            try:
                cur = db.cursor()
                cur.execute('SELECT id FROM products WHERE id=%s AND active=TRUE', (product_id,))
                if not cur.fetchone():
                    db.rollback()
                    return self.send_json({'error': 'Producto no encontrado o inactivo'}, 404)
                cur.execute('SELECT quantity FROM inventory WHERE location_id=%s AND product_id=%s FOR UPDATE', (location_id, product_id))
                row = cur.fetchone()
                current = float(row[0]) if row else 0
                new_quantity = current + quantity if movement == 'Entrada' else current - quantity
                if new_quantity < 0:
                    db.rollback()
                    return self.send_json({'error': 'Existencia insuficiente en la sede'}, 409)
                cur.execute('INSERT INTO inventory(location_id,product_id,quantity,minimum_quantity) VALUES(%s,%s,%s,0) ON DUPLICATE KEY UPDATE quantity=VALUES(quantity)', (location_id, product_id, new_quantity))
                cur.execute('INSERT INTO inventory_movements(location_id,product_id,user_id,type,quantity,note) VALUES(%s,%s,%s,%s,%s,%s)', (location_id, product_id, user['id'], movement, quantity, note))
                audit(cur, user['id'], f'{movement} de inventario', 'inventory', product_id,
                      {'location_id': location_id, 'quantity': quantity, 'note': note})
                db.commit()
            except mysql.connector.Error as error:
                db.rollback()
                print(f'[API] No fue posible registrar el movimiento de inventario: {error}')
                return self.send_json({'error': 'No fue posible registrar el movimiento de inventario'}, 500)
            finally:
                db.close()
            return self.send_json({'product_id': product_id, 'location_id': location_id, 'stock': new_quantity}, 201)
        if path == '/api/orders/close':
            cashier = self.require_user(['Cajero', 'Administrador'])
            if not cashier: return
            location_id = self.active_location(cashier)
            order_id = data.get('order_id')
            if not location_id or isinstance(order_id, bool) or not isinstance(order_id, int):
                return self.send_json({'error': 'Pedido o sede invalido'}, 400)
            db = connection()
            try:
                cur = db.cursor()
                cur.execute('SELECT table_id,total,status FROM orders WHERE id=%s AND location_id=%s FOR UPDATE',
                            (order_id, location_id))
                row = cur.fetchone()
                if not row or row[2] != 'Pagado':
                    db.rollback()
                    return self.send_json({'error': 'El pedido requiere un pago y debe estar pendiente de cierre'}, 409)
                table_id, total = row[0], row[1]
                cur.execute("UPDATE orders SET status='Cerrado',closed_at=NOW() WHERE id=%s", (order_id,))
                cur.execute("UPDATE tables_bar SET status='Libre' WHERE id=%s AND location_id=%s AND status='Ocupada'",
                            (table_id, location_id))
                if cur.rowcount != 1:
                    db.rollback()
                    return self.send_json({'error': 'No fue posible liberar la mesa del pedido'}, 409)
                invoice_number = f'FV-{order_id:07d}'
                cur.execute('INSERT INTO invoices(order_id,invoice_number) VALUES(%s,%s)', (order_id, invoice_number))
                audit(cur, cashier['id'], 'Cerrar pedido y generar factura', 'orders', order_id,
                      {'location_id': location_id, 'table_id': table_id, 'total': float(total), 'invoice': invoice_number})
                db.commit()
            except mysql.connector.IntegrityError:
                db.rollback()
                return self.send_json({'error': 'El pedido ya fue cerrado o tiene una factura'}, 409)
            except mysql.connector.Error as error:
                db.rollback()
                print(f'[API] No fue posible cerrar el pedido: {error}')
                return self.send_json({'error': 'No fue posible cerrar el pedido'}, 500)
            finally:
                db.close()
            closed_at = datetime.now().isoformat()
            for order in ORDERS:
                if order['id'] == order_id:
                    order['status'] = 'Cerrado'
                    order['closed_at'] = closed_at
                    order['invoice_number'] = invoice_number
                    break
            for table in TABLES:
                if table['id'] == table_id:
                    table['status'], table['order_id'] = 'Libre', None
                    break
            return self.send_json({'data': {'id': order_id, 'table_id': table_id, 'status': 'Cerrado',
                                            'total': float(total), 'closed_at': closed_at},
                                   'invoice': {'number': invoice_number, 'order_id': order_id}})
        self.send_json({'error': 'Ruta no encontrada'}, 404)

    def order_items(self, raw_items):
        result, total = [], 0
        for raw in raw_items:
            product = next((p for p in PRODUCTS if p['id'] == raw.get('product_id') and p['active']), None)
            quantity = int(raw.get('quantity', 0))
            if not product or quantity < 1 or quantity > product['stock']: continue
            result.append({'product_id': product['id'], 'name': product['name'], 'quantity': quantity, 'price': product['price']}); total += product['price'] * quantity
        return result, total

    def log_message(self, *_): pass

if __name__ == '__main__':
    print(f'BarWise backend iniciado en http://{HOST}:{PORT}')
    ThreadingHTTPServer((HOST, PORT), APIHandler).serve_forever()
