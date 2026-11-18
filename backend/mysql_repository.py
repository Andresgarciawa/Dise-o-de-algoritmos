"""Lectura inicial del estado desde MySQL. No contiene datos demo."""
try:
    from .mysql_database import connection
except ImportError:
    from mysql_database import connection

def load_state(location_id=1):
    db = connection()
    try:
        cur = db.cursor(dictionary=True)
        cur.execute("""SELECT u.id,u.username,u.full_name name,r.name role,u.location_id,u.active,u.password_hash password
                      FROM users u JOIN roles r ON r.id=u.role_id""")
        users = {row['username']: row for row in cur.fetchall()}
        cur.execute('SELECT id,name,address,active FROM locations'); locations = cur.fetchall()
        cur.execute("""SELECT t.id,t.location_id,CONCAT('Mesa ',LPAD(t.table_number,2,'0')) name,t.seats,t.status,o.id order_id
                       FROM tables_bar t LEFT JOIN orders o ON o.table_id=t.id AND o.status IN ('Abierto','Pagado')""")
        tables = cur.fetchall()
        cur.execute("""SELECT p.id,p.code,p.name,c.name category,p.purchase_price,p.sale_price price,p.active,
                      COALESCE(i.quantity,0) stock,sp.supplier_id,s.name supplier
                      FROM products p JOIN categories c ON c.id=p.category_id
                      LEFT JOIN inventory i ON i.product_id=p.id AND i.location_id=%s
                      LEFT JOIN supplier_products sp ON sp.product_id=p.id
                      LEFT JOIN suppliers s ON s.id=sp.supplier_id
                      ORDER BY p.name""", (location_id,))
        products = cur.fetchall()
        cur.execute("""SELECT o.id,o.location_id,o.table_id,CONCAT('Mesa ',LPAD(t.table_number,2,'0')) table_name,
                       u.full_name waiter,o.status,o.total,o.opened_at created_at,
                       p.method,p.paid_at,p.cashier_id,i.invoice_number
                       FROM orders o JOIN tables_bar t ON t.id=o.table_id
                       JOIN users u ON u.id=o.waiter_id
                       LEFT JOIN payments p ON p.order_id=o.id
                       LEFT JOIN invoices i ON i.order_id=o.id
                       WHERE o.location_id=%s AND o.status IN ('Abierto','Pagado')
                       ORDER BY o.opened_at DESC""", (location_id,))
        orders = cur.fetchall()
        items_by_order = {order['id']: [] for order in orders}
        if items_by_order:
            placeholders = ','.join(['%s'] * len(items_by_order))
            cur.execute(f"SELECT oi.order_id,oi.product_id,p.name,oi.quantity,oi.unit_price price FROM order_items oi JOIN products p ON p.id=oi.product_id WHERE oi.order_id IN ({placeholders})", tuple(items_by_order))
            for item in cur.fetchall():
                items_by_order[item['order_id']].append(item)
        for order in orders:
            order['items'] = items_by_order[order['id']]
        for order in orders:
            if order.get('created_at') is not None:
                order['created_at'] = order['created_at'].isoformat()
            if order.get('paid_at') is not None:
                order['payment'] = {'method': order.pop('method'), 'paid_at': order.pop('paid_at').isoformat(), 'cashier_id': order.pop('cashier_id')}
            else:
                order.pop('method', None)
                order.pop('paid_at', None)
                order.pop('cashier_id', None)
        return users, locations, tables, products, orders
    finally:
        db.close()

def load_products(location_id):
    db = connection()
    try:
        cur = db.cursor(dictionary=True)
        cur.execute("""SELECT p.id,p.code,p.name,c.name category,p.purchase_price,p.sale_price price,p.active,
                       COALESCE(i.quantity,0) stock,sp.supplier_id,s.name supplier
                       FROM products p JOIN categories c ON c.id=p.category_id
                       LEFT JOIN inventory i ON i.product_id=p.id AND i.location_id=%s
                       LEFT JOIN supplier_products sp ON sp.product_id=p.id
                       LEFT JOIN suppliers s ON s.id=sp.supplier_id
                       ORDER BY p.name""", (location_id,))
        return cur.fetchall()
    finally:
        db.close()

def load_suppliers():
    db = connection()
    try:
        cur = db.cursor(dictionary=True)
        cur.execute('SELECT id,identification,name,country,city,phone,active FROM suppliers ORDER BY name')
        return cur.fetchall()
    finally:
        db.close()
