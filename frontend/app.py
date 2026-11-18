from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote, urlparse, parse_qs, urlencode
from html import escape
import re
import secrets
import time
import os
from datetime import datetime
try:
    from .config import NAV, ROLE_ALLOWED
    from .api_client import request, download
except ImportError:
    from config import NAV, ROLE_ALLOWED
    from api_client import request, download

TABLES = []
LOCATIONS = []
PRODUCTS = []
SUPPLIERS = []
USERS_FRONT = []
TABLE_IDS = {}
TABLE_DETAILS = []
LOCATION_IDS = []
LOCATION_ACTIVE = {}
CATEGORIES = []
PAYMENT_METHODS = []
ORDERS_FRONT = []
SESSIONS = {}
BOOTSTRAP_CACHE = {}
METADATA_CACHE = {}
ACTIVE_LOCATION_ID = 1
CURRENT_USER_NAME = 'Andrés Martínez'

UI_TRANSLATIONS = {
    'Gestion para crecer': 'Management that grows with you',
    '¿Necesitas ayuda?': 'Need help?',
    'Consulta el centro de soporte': 'Visit the support center',
    'Cerveza Artesanal': 'Craft Beer',
    'Cerveza artesanal': 'Craft Beer',
    'Copa de Vino': 'Wine Glass',
    'Gin Tonic': 'Gin and Tonic',
    'Whisky Old Fashioned': 'Whisky Old Fashioned',
    'Nuevo pedido': 'New order',
    'Editar pedido': 'Edit order',
    'Productos en el pedido': 'Products in this order',
    'Productos actuales': 'Current products',
    'Productos disponibles': 'Available products',
    'Selecciona un producto': 'Select a product',
    'Quitar': 'Remove',
    'Agregar otro producto': 'Add another product',
    'Guardar cambios': 'Save changes',
    'Registrar pedido': 'Create order',
    'Registrar pago': 'Record payment',
    'Confirmar pago': 'Confirm payment',
    'Seleccionar': 'Select',
    'Guardar entrada': 'Save stock entry',
    'Guardar salida': 'Save stock removal',
    'Motivo': 'Reason',
    'Nota': 'Note',
    'Sin pago': 'No payment',
    'No registrado': 'Not recorded',
    'No hay productos disponibles.': 'No products available.',
    'No hay mesas libres': 'No available tables',
    'No hay usuarios para mostrar.': 'No users to display.',
    'Iniciar pedido': 'Start order',
    'Ver pedido': 'View order',
    'Ver detalle': 'View details',
    'Ver detalles': 'View details',
    'Seleccionar pedido': 'Select order',
    'Nuevo registro': 'New record',
    'Módulo operativo': 'Operations module',
    'Modulo operativo': 'Operations module',
    'Gestiona esta parte de BarWise desde un solo lugar.': 'Manage this part of BarWise from one place.',
    'Revisar ahora': 'Review now',
    'Comparativo de los últimos 7 días': 'Last 7 days comparison',
    'Gráfico de ventas de los últimos siete días': 'Sales chart for the last seven days',
    'Opciones disponibles por perfil': 'Available options by role',
    'Solo el administrador puede asignar el perfil y la sede.': 'Only the administrator can assign the role and location.',
    'Seleccione sede': 'Select location',
    'Seleccione un producto': 'Select a product',
    'Valor compra / Valor venta': 'Purchase price / Sale price',
    'Sin proveedor': 'No supplier',
    'Cambiar estado': 'Change status',
    'Administrar': 'Manage',
    'Generar reporte': 'Generate report',
    'Exportar a Excel': 'Export to Excel',
    'No se encontró el pedido seleccionado en la sede activa.': 'The selected order was not found at the active location.',
    'La factura no ha sido generada. Cierra el pedido pagado para generarla.': 'The invoice for this order has not been generated.',
    'La factura para este pedido no ha sido generada.': 'The invoice for this order has not been generated.',
    'El pago se registró, pero no fue posible cargar la factura. Intenta abrir el pedido nuevamente.': 'Payment was recorded, but the invoice could not be loaded. Open the order again to retry.',
    'Solo el Mesero puede registrar pedidos': 'Authenticated users can create orders.',
    'No hay productos activos con existencias disponibles.': 'There are no active products in stock.',
    'No hay mesas libres en esta sede.': 'There are no available tables at this location.',
    'Elige una mesa libre y define las cantidades según las existencias.': 'Choose an available table and set quantities based on stock.',
    'Este es el resumen de la operación de tu bar hoy.': "Here is your bar's operations summary for today.",
    'Todos los módulos, sedes, productos, inventario y reportes.': 'All modules, locations, products, inventory, and reports.',
    'Pedidos, pagos, facturas y reportes de pedido.': 'Orders, payments, invoices, and order reports.',
    'Mesas, tomar pedido y disponibilidad.': 'Tables, taking orders, and availability.',
    'Consulta y gestiona los pedidos activos de la sede.': 'View and manage active orders at this location.',
    'Consulta las bebidas disponibles para agregarlas a un pedido.': 'View the beverages available to add to an order.',
    'Activa o desactiva los medios disponibles al registrar pagos.': 'Enable or disable the payment methods available when recording payments.',
    'Selecciona un pedido para revisar el detalle, registrar el pago y cerrarlo.': 'Select an order to review its details, record payment, and close it.',
    'Solo el administrador puede asignar el perfil y la sede.': 'Only an administrator can assign a role and location.',
    'Comparativo de los últimos 7 días': 'Comparison for the last 7 days',
    'Opciones disponibles por perfil': 'Options available by role',
    'No hay medios de pago activos.': 'There are no active payment methods.',
    'No hay pedidos pendientes.': 'There are no pending orders.',
    'No hay pedidos activos.': 'There are no active orders.',
    'No hay usuarios para mostrar.': 'There are no users to display.',
    'Gráfico de ventas de los últimos siete días': 'Sales chart for the last seven days',
    'Formulario de registro abierto.': 'The registration form is open.',
    'Detalle de la operación cargado.': 'Operation details loaded.',
    'Gestiona esta parte de BarWise desde un solo lugar.': 'Manage this part of BarWise from one place.',
    'BarWise - Configuración': 'BarWise - Settings',
    'BarWise / Configuración': 'BarWise / Settings',
    'BarWise - Resumen': 'BarWise - Dashboard',
    'BarWise / Resumen': 'BarWise / Dashboard',
    'BarWise / Configuración / Categorías': 'BarWise / Settings / Categories',
    'BarWise / Configuración / Métodos de pago': 'BarWise / Settings / Payment methods',
    'Configuración / Categorías': 'Settings / Categories',
    'Configuración / Métodos de pago': 'Settings / Payment methods',
    'Pedidos / Registrar pago': 'Orders / Record payment',
    'Pedidos / Tomar pedido': 'Orders / Take an order',
    'Pedidos / Factura': 'Orders / Invoice',
    'Pedidos / Detalle del pedido': 'Orders / Order details',
    'Pedidos / Pendientes': 'Orders / Pending',
    'Mesas / Estado': 'Tables / Status',
    'Productos / Disponibilidad': 'Products / Availability',
    'N.º pedido': 'Order No.',
    'Medio de pago: Efectivo': 'Payment method: Cash',
    'Medio de pago: Credito': 'Payment method: Credit',
    'Medio de pago: Debito': 'Payment method: Debit',
    'Medio de pago: No registrado': 'Payment method: Not recorded',
    'Pedido registrado correctamente': 'Order created successfully.',
    'Productos agregados al pedido correctamente': 'Products added to the order successfully.',
    'Usuario registrado correctamente': 'User created successfully.',
    'Usuario actualizado correctamente': 'User updated successfully.',
    'Producto registrado correctamente': 'Product created successfully.',
    'Proveedor registrado correctamente': 'Supplier created successfully.',
    'Cambios guardados correctamente': 'Changes saved successfully.',
    'Movimiento registrado correctamente': 'Inventory movement recorded successfully.',
    'Pago registrado correctamente': 'Payment recorded successfully.',
    'Pedido cerrado correctamente': 'Order closed successfully.',
    'No fue posible registrar el pedido': 'Could not create the order.',
    'No fue posible agregar productos al pedido': 'Could not add products to the order.',
    'No fue posible registrar el usuario': 'Could not create the user.',
    'No fue posible actualizar el usuario': 'Could not update the user.',
    'No fue posible registrar el producto': 'Could not create the product.',
    'No fue posible registrar el proveedor': 'Could not create the supplier.',
    'No fue posible guardar los cambios': 'Could not save the changes.',
    'No fue posible registrar el movimiento': 'Could not record the inventory movement.',
    'No fue posible registrar el pago': 'Could not record the payment.',
    'No fue posible cerrar el pedido': 'Could not close the order.',
    'Selecciona una mesa libre': 'Select an available table',
    'Selecciona un producto': 'Select a product',
    'Seleccione sede': 'Select a location',
    'Sin proveedor': 'No supplier',
    'Buscar por pedido, mesa, mesero o producto…': 'Search by order, table, waiter, or product…',
    'Pendiente de pago': 'Payment pending',
    'Pagado · pendiente de cierre': 'Paid · pending closure',
    'Valor de compra': 'Purchase price',
    'Valor de venta': 'Sale price',
    'Cierra el pedido pagado': 'Close the paid order',
    'Parametrización del sistema': 'System configuration',
    'Gestión de productos': 'Product management',
    'Gestión de proveedores': 'Supplier management',
    'Gestión de usuarios': 'User management',
    'Gestión de sedes': 'Location management',
    'Gestión de mesas': 'Table management',
    'Estado de mesas': 'Table status',
    'Disponibilidad de productos': 'Product availability',
    'Datos del movimiento': 'Movement details',
    'Existencias recientes': 'Recent stock movements',
    'Alertas de inventario': 'Inventory alerts',
    'Rendimiento de ventas': 'Sales performance',
    'Registrar otro producto': 'Register another product',
    'Registrar categoría': 'Add category',
    'Registrar proveedor': 'Add supplier',
    'Registrar producto': 'Add product',
    'Registrar usuario': 'Add user',
    'Registrar sede': 'Add location',
    'Registrar mesa': 'Add table',
    'Registrar pedido': 'Create order',
    'Registrar pago': 'Record payment',
    'Agregar productos al pedido': 'Add products to order',
    'Productos en el pedido': 'Products already in this order',
    'Productos actuales': 'Current products',
    'Productos disponibles': 'Available products',
    'Cantidad actual': 'Current quantity',
    'Ya está en el pedido': 'Already in order',
    'Agregar otro producto': 'Add another product',
    'Agregar productos': 'Add products',
    'Continuar al cierre': 'Continue to checkout',
    'Ver factura': 'View invoice',
    'Selecciona un pedido para revisar el detalle, registrar el pago y cerrarlo.': 'Select an order to review its details and record payment. The invoice is generated immediately.',
    'Cerrar pedido y generar factura': 'Close order and generate invoice',
    'La sede seleccionada no es válida': 'The selected location is invalid.',
    'No se pudo consultar el pedido': 'Could not retrieve the order.',
    'No se pudo generar el reporte': 'Could not generate the report.',
    'Nuevo pedido': 'New order',
    'Buenos días': 'Good morning',
    'Ventas del día': 'Sales today',
    'Pedidos activos': 'Active orders',
    'Tiempo promedio': 'Average time',
    'Revisar ahora': 'Review now',
    'Ventas totales': 'Total sales',
    'Pendientes de pago': 'Pending payments',
    'Pedidos cerrados': 'Closed orders',
    'Ticket promedio': 'Average order value',
    'Registros activos': 'Active records',
    'Nuevos este mes': 'New this month',
    'Actualizados hoy': 'Updated today',
    'Movimientos hoy': 'Movements today',
    'Valor inventario': 'Inventory value',
    'Resto del sistema': 'Other system settings',
    'Buscar producto': 'Search products',
    'Buscar proveedor': 'Search suppliers',
    'Buscar usuario': 'Search users',
    'Buscar pedidos': 'Search orders',
    'Buscar…': 'Search…',
    'Quitar producto': 'Remove product',
    'Tarjeta crédito': 'Credit card',
    'Tarjeta débito': 'Debit card',
    'Métodos de pago': 'Payment methods',
    'Medio de pago': 'Payment method',
    'Medio': 'Method',
    'Total a pagar': 'Total due',
    'Imprimir factura': 'Print invoice',
    'Volver a pedidos': 'Back to orders',
    'Factura No.': 'Invoice No.',
    'Comprobante interno de venta': 'Internal sales receipt',
    'La factura no ha sido generada': 'The invoice has not been generated',
    'Generar reporte': 'Generate report',
    'Exportar a Excel': 'Export to Excel',
    'Productos vendidos': 'Products sold',
    'Fecha inicial': 'Start date',
    'Fecha final': 'End date',
    'Resultados': 'Results',
    'Configuración': 'Settings',
    'Categorías': 'Categories',
    'Proveedores': 'Suppliers',
    'Usuarios': 'Users',
    'Sedes': 'Locations',
    'Reportes': 'Reports',
    'Inventario': 'Inventory',
    'Productos': 'Products',
    'Pedidos': 'Orders',
    'Mesas': 'Tables',
    'Resumen': 'Dashboard',
    'Ingreso': 'Sign in',
    'Iniciar sesión': 'Sign in',
    'Ingresar': 'Log in',
    'Cerrar sesión': 'Log out',
    'Necesitas ayuda?': 'Need help?',
    '¿Necesitas ayuda?': 'Need help?',
    'Consulta el centro de soporte': 'Visit the support center',
    'Sede activa': 'Active location',
    'Navegación principal': 'Main navigation',
    'Tomar pedido': 'Take an order',
    'Detalle del pedido': 'Order details',
    'Pedidos pendientes': 'Pending orders',
    'Gestión de sedes': 'Location management',
    'Editar sede': 'Edit location',
    'Editar producto': 'Edit product',
    'Editar proveedor': 'Edit supplier',
    'Editar usuario': 'Edit user',
    'Factura': 'Invoice',
    'Pendientes': 'Pending',
    'Entrada de inventario': 'Stock entry',
    'Salida de inventario': 'Stock removal',
    'Entrada': 'Stock in',
    'Salida': 'Stock out',
    'Disponibilidad': 'Availability',
    'Disponible': 'Available',
    'No disponible': 'Unavailable',
    'Existencia': 'Stock',
    'Existencias': 'Stock',
    'Cantidad': 'Quantity',
    'Disminuir cantidad': 'Decrease quantity',
    'Aumentar cantidad': 'Increase quantity',
    'Cant.': 'Qty.',
    'Producto': 'Product',
    'Proveedor': 'Supplier',
    'Categoría': 'Category',
    'Nombre de sede': 'Location name',
    'Número de mesa': 'Table number',
    'Sede': 'Location',
    'Dirección': 'Address',
    'Identificación': 'Tax ID',
    'País': 'Country',
    'Ciudad': 'City',
    'Contacto': 'Contact',
    'Código': 'Code',
    'Precio': 'Price',
    'Estado': 'Status',
    'Acciones': 'Actions',
    'Acción': 'Action',
    'Fecha': 'Date',
    'Pedido': 'Order',
    'Mesa': 'Table',
    'Mesero': 'Waiter',
    'Cajero': 'Cashier',
    'Administrador': 'Administrator',
    'Perfil': 'Role',
    'Usuario': 'Username',
    'Contraseña': 'Password',
    'Nueva contraseña (opcional)': 'New password (optional)',
    'Nombre': 'Name',
    'Guardar cambios': 'Save changes',
    'Guardar': 'Save',
    'Cancelar': 'Cancel',
    'Cerrar': 'Close',
    'Editar': 'Edit',
    'Activo': 'Active',
    'Activa': 'Active',
    'Inactivo': 'Inactive',
    'Libre': 'Available',
    'Ocupada': 'Occupied',
    'Abierto': 'Open',
    'Cerrado': 'Closed',
    'Hoy': 'Today',
    'Vie': 'Fri',
    'Sáb': 'Sat',
    'Dom': 'Sun',
    'Lun': 'Mon',
    'Mar': 'Tue',
    'Mié': 'Wed',
    'Pagado': 'Paid',
    'Pendiente': 'Pending',
    'Generada': 'Generated',
    'Efectivo': 'Cash',
    'Credito': 'Credit',
    'Debito': 'Debit',
    'Seleccionar': 'Select',
    'Seleccionar pedido': 'Select order',
    'Selecciona': 'Select',
    'Buscar': 'Search',
    'Registrar': 'Record',
    'Administrar': 'Manage',
    'Ver detalles': 'View details',
    'Ver detalle': 'View details',
    'Ver pedido': 'View order',
    'Iniciar pedido': 'Start order',
    'Nuevo registro': 'New record',
    'Pagar': 'Pay',
    'Guardar entrada': 'Save stock entry',
    'Guardar salida': 'Save stock removal',
    'Cambiar estado': 'Change status',
    'Nota': 'Note',
    'Motivo': 'Reason',
    'Puestos': 'Seats',
    'stock': 'stock',
    'Todos': 'All',
    'Sin sede': 'No location',
    'Todas': 'All locations',
    'No registrado': 'Not recorded',
    'Gestión': 'Management',
    'Modulo operativo': 'Operations',
    'barwise': 'BarWise',
}

def safe(value):
    return escape(str(value), quote=True)

def translate_text(value):
    stripped = value.strip()
    if stripped in UI_TRANSLATIONS:
        return value.replace(stripped, UI_TRANSLATIONS[stripped])
    for spanish, english in sorted(UI_TRANSLATIONS.items(), key=lambda item: len(item[0]), reverse=True):
        if not any(character.isspace() for character in spanish):
            continue
        value = re.sub(rf'(?<!\w){re.escape(spanish)}(?!\w)', english, value)
    value = re.sub(r'\bMesa (?=\d)', 'Table ', value)
    value = re.sub(r'\bPedido (?=#|\d)', 'Order ', value)
    value = value.replace(' · Libre', ' · Available').replace(' · Abierto', ' · Open')
    value = value.replace('Estado: ', 'Status: ').replace('Mesero: ', 'Waiter: ')
    value = value.replace(' · Administrador', ' · Administrator')
    value = value.replace(' · Cajero', ' · Cashier')
    value = value.replace(' · Mesero', ' · Waiter')
    count_words = {
        'registradas': ('location', 'locations'),
        'mesas': ('table', 'tables'),
        'categorías': ('category', 'categories'),
        'productos': ('product', 'products'),
        'proveedores': ('supplier', 'suppliers'),
        'activos': ('active', 'active'),
    }
    value = re.sub(
        r'\b(\d+)\s+(registradas|mesas|categorías|productos|proveedores|activos)\b',
        lambda match: f'{match.group(1)} {count_words[match.group(2)][0 if match.group(1) == "1" else 1]}',
        value,
    )
    return value

def english_markup(markup):
    markup = markup.replace('lang="es"', 'lang="en"')
    markup = markup.replace('value="Sede activa"', 'value="Active location"')
    chunks = re.split(r'(<script\b.*?</script>)', markup, flags=re.IGNORECASE | re.DOTALL)
    for index in range(0, len(chunks), 2):
        chunk = re.sub(r'>([^<>]+)<', lambda match: '>' + translate_text(match.group(1)) + '<', chunks[index])
        chunk = re.sub(
            r'(placeholder|aria-label)="([^"]*)"',
            lambda match: f'{match.group(1)}="{translate_text(match.group(2))}"',
            chunk,
        )
        chunks[index] = chunk
    return ''.join(chunks)

def append_notice(markup, notice):
    return english_markup(markup.replace('</section>', f'<div class="notice">{notice}</div></section>'))

def invalidate_user_cache(user):
    prefix = f"{user.get('username', '')}:"
    for key in tuple(BOOTSTRAP_CACHE):
        if key.startswith(prefix):
            BOOTSTRAP_CACHE.pop(key, None)
    for key in tuple(METADATA_CACHE):
        if key.startswith(prefix):
            METADATA_CACHE.pop(key, None)

def refresh_frontend_data(user, location_id_override=None):
    global TABLES, LOCATIONS, LOCATION_IDS, LOCATION_ACTIVE, PRODUCTS, SUPPLIERS, CATEGORIES, PAYMENT_METHODS
    global TABLE_IDS, TABLE_DETAILS, ORDERS_FRONT, USERS_FRONT, ACTIVE_LOCATION_ID
    location_id = location_id_override or user.get('active_location_id', user.get('location_id') or 1)
    status, data, _ = request('/api/bootstrap', cookie=user['backend_cookie'], location_id=location_id)
    if status != 200:
        return status
    TABLES = [(table['name'], table['status'], f"{table['seats']} puestos") for table in data.get('tables', [])]
    TABLE_IDS = {table['name']: table['id'] for table in data.get('tables', [])}
    TABLE_DETAILS = data.get('tables', [])
    LOCATIONS = [(location['name'], location['address']) for location in data.get('locations', [])]
    LOCATION_IDS = [location['id'] for location in data.get('locations', [])]
    LOCATION_ACTIVE = {location['id']: location.get('active', True) for location in data.get('locations', [])}
    PRODUCTS = data.get('products', [])
    ORDERS_FRONT = data.get('orders', [])
    ACTIVE_LOCATION_ID = data.get('active_location_id', location_id)
    BOOTSTRAP_CACHE[f"{user.get('username', '')}:{location_id}"] = (time.time(), data)
    return status
CSS = '''
*{box-sizing:border-box}
body{display:flex;min-height:100vh;margin:0;background:#f7f5f0;color:#282725;font:14px Arial,sans-serif}
.side{display:flex;flex:0 0 205px;flex-direction:column;min-height:100vh;padding:22px 14px;background:#fffdf9;border-right:1px solid #e7e1d8}
.brand{display:flex;gap:9px;align-items:center;margin:0 5px 23px}
.logo{display:inline-flex;align-items:center;justify-content:center;width:29px;height:29px;border-radius:7px;background:#b85f35;color:#fff;font:bold 20px Georgia}
.brand b{font:bold 20px Georgia}
.muted{display:block;margin-top:4px;color:#928c83;font-size:11px}
.location-form,.location-fixed{margin-bottom:17px;padding:10px;background:#f0ddd1;border-radius:8px;color:#814225}
.location-form label,.location-fixed b{display:block;margin:0 0 4px;font-size:11px;font-weight:bold}
.location-form select{width:100%;padding:4px;border:0;background:transparent;color:#6c4533;font-size:11px}
.location-fixed span{display:block;font-size:11px;line-height:1.5}
.nav a{display:block;margin:2px 0;padding:9px 11px;border-radius:7px;color:#6c6962;text-decoration:none}
.nav a:hover{background:#f5eee7}
.nav a.active{background:#f0ddd1;color:#93431f;font-weight:bold}
.support{margin-top:auto;padding:14px 5px 0;border-top:1px solid #e7e1d8;color:#5e5a54;font-size:12px}
.support small{display:block;margin:5px 0 12px;color:#817b73;font-size:11px}
.main{flex:1;min-width:0}
header{display:flex;align-items:center;justify-content:space-between;min-height:62px;padding:0 34px;border-bottom:1px solid #e7e1d8;background:#fff;color:#817b73}
.user{display:flex;align-items:center;color:#282725;font-size:12px;font-weight:bold}
.user .muted{margin-left:5px;font-weight:normal}
.avatar{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;margin-right:8px;border-radius:50%;background:#d8c1a7;color:#795c3b;font-size:11px}
.content{max-width:1450px;margin:0 auto;padding:30px 34px}
.top{display:flex;align-items:center;justify-content:space-between;margin-bottom:22px}
.kicker{color:#b85f35;font-size:11px;font-weight:bold;letter-spacing:.07em;text-transform:uppercase}
.title{margin:7px 0 5px;font:700 30px Georgia,serif}
.desc{margin:0;color:#817b73}
.btn{display:inline-block;padding:10px 15px;border:0;border-radius:6px;background:#b85f35;color:#fff;text-align:center;text-decoration:none;font-weight:bold;cursor:pointer}
.btn:hover{background:#8f431f}
.outline{display:inline-block;padding:8px 12px;border:1px solid #d8d1c7;border-radius:6px;background:#fff;color:#594f45;text-align:center;text-decoration:none;font-size:12px;font-weight:bold;cursor:pointer}
.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin-bottom:18px}
.stat,.card{border:1px solid #e7e1d8;border-radius:9px;background:#fff}
.stat{padding:14px 16px}
.stat small{color:#817b73}
.stat strong{display:block;margin:6px 0;font-size:21px}
.up{color:#428263;font-size:11px}
.warn{color:#bd6845;font-size:11px}
.dashboard-layout{display:grid;grid-template-columns:1fr 1.45fr;gap:14px}
.roles-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:20px}
.role-summary{padding-top:13px;border-top:1px solid #eee9e2}
.role-summary h4{margin:0 0 6px;font-size:12px}
.role-summary p{margin:0;color:#817b73;font-size:11px;line-height:1.5}
.cols{display:grid;grid-template-columns:minmax(230px,.85fr) minmax(0,1.7fr);gap:14px;margin-bottom:18px}
.card{min-width:0;padding:18px}
.card h3{margin:0 0 5px;font-size:15px}
.card p{margin:0;color:#817b73;font-size:12px}
.bars{display:flex;height:145px;align-items:end;gap:13px;margin-top:11px;padding:16px 12px 0;border-bottom:1px solid #eee9e2}
.bars i{display:block;flex:1;border-radius:4px 4px 0 0;background:#d8ac95}
.bars i:last-child{background:#b85f35}
.days{display:flex;justify-content:space-around;margin-top:7px;color:#a19b92;font-size:10px}
.notice{margin-bottom:16px;padding:12px;border-radius:7px;background:#f8eadf;color:#854827;font-size:12px}
.module-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.module{min-height:145px;padding:18px}
.module .icon{margin-bottom:12px;color:#b85f35;font-size:23px}
.module a{margin-top:14px}
.table-status-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-top:14px}
.table-status{display:flex;justify-content:space-between;padding:12px;border:1px solid #e7e1d8;border-radius:7px;color:inherit;text-decoration:none}
.table-status .libre{color:#478467}.table-status .ocupada{color:#b85f35}
.selected-table{display:flex;align-items:center;gap:8px;margin-top:14px}
.selected-table .btn{margin-left:auto}
.status-ok,.status-off{display:inline-block;padding:4px 8px;border-radius:14px;font-size:11px;white-space:nowrap}
.status-ok{background:#e2f1e7;color:#327550}
.status-off{background:#f5dfd7;color:#a84d2b}
.search-form{display:flex;align-items:center;gap:8px}
.search-form input{flex:1;min-width:0}
form:not(.search-form):not(.location-form){display:flex;flex-direction:column;align-items:stretch}
form label{display:block;margin:7px 0;color:#59544d;font-size:12px}
form input,form select{display:block;width:100%;margin-top:5px;padding:9px 10px;border:1px solid #ddd5ca;border-radius:6px;background:#fff;color:#282725}
.location-form select{margin:0}
.card form:not(.search-form) .btn{width:100%;margin-top:8px}
table{width:100%;margin-top:14px;border-collapse:collapse;font-size:12px}
th{text-align:left;color:#817b73;background:#faf7f2;font-weight:normal}
th,td{padding:10px 9px}
td{border-top:1px solid #eee9e2}
.form-row{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;width:100%}
form.form-row:not(.search-form):not(.location-form){display:grid;grid-template-columns:repeat(4,minmax(0,1fr));align-items:end;gap:10px}
.order-form{display:block}
.order-layout{display:grid;grid-template-columns:minmax(0,2fr) minmax(250px,1fr);gap:16px}
.order-layout .card{margin-bottom:14px}
.products-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:14px}
.product-card{display:flex;flex-direction:column;overflow:hidden;padding:0;border:1px solid #e7e1d8;border-radius:12px;background:#fff;cursor:pointer;transition:transform .15s,box-shadow .15s}
.product-card:hover{transform:translateY(-2px);box-shadow:0 8px 18px #392b1d18}
.product-card .product-image{display:block;width:100%;height:120px;object-fit:cover;background:#f6e8df}
.product-card .product-info{display:flex;flex-direction:column;gap:7px;padding:12px}
.product-card .product-name{font-weight:bold;min-height:32px}
.product-card .product-select{position:absolute;opacity:0}
.product-card.selected{outline:2px solid #b85f35}
.modal-product-search{margin:12px 0;width:100%}.modal-products-grid{max-height:390px;overflow:auto;padding:2px}.modal-product-card .product-info input{width:70px;display:inline-block;margin-left:6px;padding:5px}.modal-product-card .product-info span:last-child{color:#59544d;font-size:12px}
.product-card input{align-self:flex-end;width:auto}
.product-card span{color:#555}
.product-card em{width:max-content;font-style:normal}
.order-detail{height:max-content}
.total-line{display:flex;justify-content:space-between;margin-top:20px;padding:15px 0;border-top:1px solid #eee}
.order-detail .btn{width:100%}
.payment-layout{display:grid;grid-template-columns:1.4fr 1fr;gap:16px}
.payment-options{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin-top:14px}
.payment-options label{padding:16px 8px;border:1px solid #e7e1d8;border-radius:8px;text-align:center;cursor:pointer;font-size:13px}
.payment-options label:has(input:checked){border-color:#b85f35}
.payment-options input{position:absolute;width:1px;height:1px;opacity:0}
.payment-options b,.payment-options span{display:block}
.payment-options span{margin-top:7px;color:#5e5a54;font-size:12px}
.pay-total{display:flex;align-items:center;justify-content:space-between;margin:20px 0;font-size:20px}
.payment-layout .btn{width:100%}
.login{width:min(390px,calc(100vw - 32px));padding:30px;background:#fff;border:1px solid #eee9e2;border-radius:9px}
.login h1{margin:12px 0 6px;font:700 25px Georgia,serif}
.login .muted{margin:0 0 14px}
.login input{margin:5px 0 10px}
.login button{width:100%;margin-top:6px}
@media(max-width:1050px){.side{flex-basis:150px}.content{padding:22px 18px}.title{font-size:26px}.stat strong{font-size:18px}.module-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.table-status-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:760px){.side{flex-basis:165px;padding:18px 10px}.content{padding:20px 16px}header{padding:0 18px}.dashboard-layout,.cols,.payment-layout,.order-layout{grid-template-columns:1fr}.form-row,form.form-row{grid-template-columns:1fr 1fr}.products-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.stats{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:560px){body{display:block}.side{min-height:0;padding:10px;border-right:0;border-bottom:1px solid #e7e1d8}.brand{margin:0 0 10px}.location-form,.location-fixed{margin-bottom:8px}.nav{display:flex;overflow-x:auto;gap:3px}.nav a{flex:0 0 auto;margin:0;padding:8px}.support{display:none}header{min-height:54px;padding:0 14px}.user .muted{display:none}.content{padding:18px 12px}.top{align-items:flex-start;gap:12px}.title{font-size:25px}.stats{gap:8px}.stat{padding:11px}.stat strong{font-size:17px}.roles-grid,.module-grid{grid-template-columns:1fr}.table-status-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.form-row,form.form-row{grid-template-columns:1fr}.payment-options{grid-template-columns:1fr 1fr}table{display:block;overflow-x:auto;white-space:nowrap}}
'''
UI_CSS = '''
.search-form .outline{flex:0 0 auto}
.tabs{margin:14px 0 18px}
.products-grid{grid-template-columns:repeat(3,minmax(0,1fr))}
@media print{body{display:block;background:#fff;color:#222}.side,header,.invoice-page .top,.invoice-page .screen-only{display:none!important}.invoice-page{padding:0!important;margin:0!important}.invoice-page .invoice-card{width:80mm;max-width:80mm;margin:0 auto;border:0;box-shadow:none;padding:5mm;background:#fff}.invoice-page .invoice-logo{width:22mm;height:22mm;margin:0 auto 3mm;display:block!important}.invoice-page .invoice-brand{text-align:center}.invoice-page table{font-size:10px}.invoice-page th,.invoice-page td{padding:2mm 0;border-top:1px solid #ddd}.invoice-page .invoice-divider{border:0;border-top:1px dashed #888;margin:3mm 0}.invoice-page .pay-total{font-size:16px;margin:3mm 0}.invoice-page .status-ok{padding:0;background:none;color:#222}}
@media(max-width:800px){.products-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:560px){.products-grid{grid-template-columns:1fr}}
'''
UI_CSS += '''
.payment-options label:has(input:checked){border-width:2px}
.order-tables-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,240px),1fr));gap:16px;margin-top:18px}
.order-table-card{display:flex;min-height:160px;flex-direction:column;justify-content:space-between;padding:18px;border:1px solid #e7e1d8;border-radius:10px;background:#fff;color:inherit;text-align:left;font:inherit;box-shadow:0 2px 6px #21180f0a}
.order-table-card.is-actionable{cursor:pointer;transition:border-color .15s,box-shadow .15s}
.order-table-card.is-actionable:hover,.order-table-card.is-actionable:focus-visible{border-color:#b85f35;box-shadow:0 0 0 2px #b85f3522;outline:0}
.order-table-name{font-size:18px;font-weight:bold}
.order-table-card p{margin:8px 0 0;color:#817b73;font-size:12px}
.order-table-card .status-ok,.order-table-card .status-off{margin-top:9px}
.invoice-card{max-width:760px;margin:0 auto;position:relative}.invoice-logo{display:block;width:84px;height:84px;max-width:84px;max-height:84px;object-fit:contain;margin:0 auto 12px}.invoice-brand{text-align:center;margin:0 0 16px}.invoice-brand h2{margin:0 0 4px;font:700 25px Georgia,serif}.invoice-brand p{margin:2px 0;color:#817b73}.invoice-meta{display:grid;grid-template-columns:1fr 1fr;gap:4px 20px;padding:12px 0;border-top:1px dashed #d8d0c5;border-bottom:1px dashed #d8d0c5}.invoice-meta p{margin:2px 0;font-size:12px}.invoice-divider{border:0;border-top:1px dashed #d8d0c5;margin:16px 0}.invoice-actions{display:flex;gap:10px;justify-content:flex-end;margin-top:18px}.invoice-actions .btn,.invoice-actions .outline{width:auto}.invoice-card table{margin-top:0}.invoice-card .pay-total{border-top:0;margin-top:10px;padding-top:10px}
.modal-product-card{position:relative}.modal-product-card .product-info>span{display:block!important}.modal-product-card .quantity-control{display:flex!important;align-items:center;gap:6px;margin-top:4px;color:#59544d;font-size:12px}.modal-product-card .quantity-control input{display:inline-block!important;visibility:visible!important;opacity:1!important;width:72px!important;height:34px;margin:0;padding:6px 8px;border:1px solid #d8d0c5;border-radius:6px;background:#fff;color:#282725;font:inherit}.modal-product-card .product-select:checked~.product-image{outline:3px solid #b85f35;outline-offset:-3px}.modal-product-card .product-select:checked~.product-info{background:#fffaf6}
.modal-product-card .quantity-control{justify-content:flex-start}.modal-product-card .quantity-control button{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;padding:0;border:1px solid #d8d0c5;border-radius:6px;background:#fff;color:#b85f35;font-size:20px;line-height:1;cursor:pointer}.modal-product-card .quantity-control button:hover{background:#f8e9df}.modal-product-card .quantity-control input{text-align:center}.modal-product-card .quantity-control input::-webkit-inner-spin-button,.modal-product-card .quantity-control input::-webkit-outer-spin-button{opacity:1}
.order-table-heading{display:flex;align-items:center;justify-content:space-between;gap:8px}
.order-table-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.order-table-action{display:inline-block;padding:11px 14px;border:0;border-radius:6px;background:#b85f35;color:#fff;text-decoration:none;font:inherit;font-size:14px;font-weight:bold;cursor:pointer}
.order-table-action:hover{background:#8f431f}
.order-table-action.secondary{border:1px solid #d8d1c7;background:#fff;color:#594f45}
.content,.main{min-width:0}.card{min-width:0;overflow:hidden}.modal{overflow:auto}.modal-products-grid{grid-template-columns:repeat(3,minmax(0,1fr));max-height:calc(100vh - 230px)}
@media(max-width:900px){.module-grid,.products-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.modal-products-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.content{padding-left:24px;padding-right:24px}}
@media(max-width:640px){.side{flex-basis:180px}.content{padding:16px 12px}.top{flex-wrap:wrap}.top>.outline,.top>.btn{width:100%;text-align:center}.user{max-width:48%;text-align:right}.user strong{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.modal{width:calc(100vw - 16px);max-height:calc(100vh - 16px);border-radius:8px}.modal-content{padding:16px}.modal-header h2{font-size:20px}.modal-products-grid{grid-template-columns:1fr;max-height:calc(100vh - 245px);gap:10px}.modal-product-card .product-image{height:110px}.modal-actions{position:sticky;bottom:0;padding-top:10px;background:#fff;z-index:2}.modal-actions .btn,.modal-actions .outline{flex:1}.invoice-meta{grid-template-columns:1fr}.invoice-actions{flex-direction:column}.invoice-actions .btn,.invoice-actions .outline{width:100%;text-align:center}.order-table-actions{flex-direction:column}.order-table-actions>*{width:100%;text-align:center}}
@media(max-width:400px){.side{padding:8px}.brand b{font-size:18px}.nav a{font-size:12px;padding:7px 8px}.content{padding:14px 8px}.title{font-size:23px}.products-grid{grid-template-columns:1fr}.form-row,form.form-row{grid-template-columns:1fr}.payment-options{grid-template-columns:1fr}.modal-product-card .product-image{height:95px}}
.modal{width:min(720px,calc(100vw - 28px));max-height:calc(100vh - 32px);padding:0;border:0;border-radius:10px;box-shadow:0 20px 60px #21180f55}
.modal::backdrop{background:#21180f77}
.modal-content{padding:22px}
.modal-header{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:15px}
.modal-header h2{margin:0;font:700 22px Georgia,serif}
.modal-close{border:0;background:transparent;font-size:24px;cursor:pointer}
.order-items{display:grid;gap:8px}
.order-item-row{display:grid;grid-template-columns:minmax(0,1fr) 110px auto;gap:8px;align-items:end}
.order-item-row label:first-child{min-width:0}
.order-item-row .product-search{margin-bottom:7px}
.order-item-row .outline{margin-bottom:2px}
.existing-order-items{margin:0 0 14px;padding:12px 14px;border:1px solid #e7e1d8;border-radius:8px;background:#faf8f5}
.existing-order-items h3{margin:0 0 8px;font-size:15px}
.existing-order-items ul{display:grid;gap:6px;margin:0;padding:0;list-style:none}
.existing-order-items li{display:flex;justify-content:space-between;gap:12px}
.existing-order-items li>span{display:flex;flex:1;justify-content:space-between;gap:12px;align-items:center}
.existing-quantity{font-weight:bold}
.order-summary-items{display:grid;gap:8px;margin:0;padding:0;list-style:none}
.order-summary-items li{display:grid;grid-template-columns:minmax(0,1fr) 60px 110px;gap:12px;padding:8px 0;border-bottom:1px solid #e7e1d8}
.order-summary-total{display:flex;justify-content:space-between;margin-top:16px}
.modal-actions{display:flex;justify-content:flex-end;gap:8px;margin-top:16px}
.modal-actions .btn{width:auto}
@media(max-width:560px){.order-item-row{grid-template-columns:minmax(0,1fr) 80px auto}}
@media(max-width:640px){.modal{width:calc(100vw - 16px);max-height:calc(100vh - 16px)}.modal-products-grid{grid-template-columns:1fr;max-height:calc(100vh - 245px)}.modal-actions .btn,.modal-actions .outline{flex:1}.invoice-actions{flex-direction:column}.invoice-actions .btn,.invoice-actions .outline{width:100%;text-align:center}.order-table-actions{flex-direction:column}.order-table-actions>*{width:100%;text-align:center}}
@media(max-width:400px){.modal-content{padding:14px}.modal-header h2{font-size:19px}.modal-product-card .product-image{height:95px}.payment-options{grid-template-columns:1fr}}
'''

def login_page(error=''):
    message = f'<p class="notice" role="alert">{safe(error)}</p>' if error else ''
    return english_markup(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Sign in | BarWise</title><style>{CSS}{UI_CSS}body{{display:grid;place-items:center;padding:16px}}.login{{align-self:center}}.login label{{font-weight:bold}}</style></head><body><form class="login" method="post" action="/login"><span class="logo" aria-hidden="true">B</span><h1>Sign in</h1>{message}<label>Username<input name="username" required autofocus autocomplete="username"></label><label>Password<input name="password" type="password" required autocomplete="current-password"></label><button class="btn" type="submit">Log in</button></form></body></html>''')

def links(active, role):
    allowed = ROLE_ALLOWED.get(role, ROLE_ALLOWED['Administrador'])
    return ''.join(f'<a class="{"active" if key == active else ""}" href="/{key}">{label}</a>' for label, key in NAV if key in allowed)

def shell(title, active, content, role='Administrador'):
    locations = ' · '.join(safe(name) for name, _ in LOCATIONS)
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BarWise - {title}</title><style>{CSS}{UI_CSS}</style></head><body><aside class="side"><div class="brand"><span class="logo">B</span><div><b>barwise</b><small class="muted">Gestion para crecer</small></div></div><div class="workspace">BM <small>Sede activa: Calle 85<br>{locations}</small></div><nav class="nav">{links(active, role)}</nav><div class="support">? &nbsp; Necesitas ayuda?<small>Consulta el centro de soporte</small><br><a href="/logout" style="color:#b85f35;text-decoration:none;font-weight:bold">Cerrar sesión</a></div></aside><main class="main"><header><span>Barwise / {title}</span><span class="user"><span class="avatar">AM</span>Andres Martinez <small class="muted">{role}</small></span></header>{content}</main></body></html>'''

def shell(title, active, content, role='Administrador'):
    locations = ' · '.join(name for name, _ in LOCATIONS)
    if role == 'Administrador':
        location_box = '<form class="location-form" method="get"><label for="active-location">Sede activa</label><select id="active-location" name="location_id" onchange="this.form.submit()">' + ''.join(f'<option value="{LOCATION_IDS[i] if i < len(LOCATION_IDS) else i + 1}" {"selected" if (LOCATION_IDS[i] if i < len(LOCATION_IDS) else i + 1) == ACTIVE_LOCATION_ID else ""}>{safe(name)}</option>' for i, (name, _) in enumerate(LOCATIONS)) + '</select></form>'
    else:
        active_name = safe(next((name for index, (name, _) in enumerate(LOCATIONS) if (LOCATION_IDS[index] if index < len(LOCATION_IDS) else index + 1) == ACTIVE_LOCATION_ID), locations))
        location_box = f'<div class="location-fixed"><b>Sede activa</b><span>{active_name}</span></div>'
    return english_markup(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BarWise - {safe(title)}</title><style>{CSS}{UI_CSS}</style></head><body><aside class="side"><div class="brand"><span class="logo" aria-hidden="true">B</span><b>barwise</b></div>{location_box}<nav class="nav" aria-label="Main navigation">{links(active, role)}</nav><div class="support">Need help?<small>Visit the support center</small><a href="/logout" style="color:#b85f35;text-decoration:none;font-weight:bold">Log out</a></div></aside><main class="main"><header><span>BarWise / {safe(title)}</span><span class="user"><span class="avatar" aria-hidden="true">AM</span><span>{safe(CURRENT_USER_NAME)}<small class="muted">{safe(role)}</small></span></span></header>{content}</main></body></html>''')

def dashboard(role='Administrador'):
    bars = ''.join(f'<i style="height:{h}%"></i>' for h in [48, 62, 54, 76, 68, 88, 72])
    today = datetime.now()
    weekdays = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
    months = ('January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December')
    date_label = f'{weekdays[today.weekday()]}, {months[today.month - 1]} {today.day}, {today.year}'
    content = f'''<section class="content"><div class="top"><div><label class="kicker">{date_label}</label><h1 class="title">Buenos días, Andrés</h1><p class="desc">Este es el resumen de la operación de tu bar hoy.</p></div><a class="btn" href="/orders">+ Nuevo pedido</a></div><div class="stats"><div class="stat"><small>Ventas del día</small><strong>$ 2,846,000</strong><span class="up">↗ 12.5%</span></div><div class="stat"><small>Pedidos activos</small><strong>18</strong><span class="up">↗ 4 new</span></div><div class="stat"><small>Tiempo promedio</small><strong>24 min</strong><span class="up">↗ -8 min</span></div><div class="stat"><small>Alertas de inventario</small><strong>6</strong><span class="warn">● Revisar ahora</span></div></div><div class="dashboard-layout"><article class="card"><h3>Rendimiento de ventas</h3><p>Comparativo de los últimos 7 días</p><div class="bars" role="img" aria-label="Gráfico de ventas de los últimos siete días">{bars}</div><div class="days"><span>Vie</span><span>Sáb</span><span>Dom</span><span>Lun</span><span>Mar</span><span>Mié</span><span>Hoy</span></div></article><article class="card"><h3>Opciones disponibles por perfil</h3><div class="roles-grid"><div class="role-summary"><h4>Administrador</h4><p>Todos los módulos, sedes, productos, inventario y reportes.</p></div><div class="role-summary"><h4>Cajero</h4><p>Pedidos, pagos, facturas y reportes de pedido.</p></div><div class="role-summary"><h4>Mesero</h4><p>Mesas, tomar pedido y disponibilidad.</p></div></div></article></div></section>'''
    return shell('Resumen', 'dashboard', content, role)

def product_image(product):
    category = str(product.get('category', '')).casefold()
    if 'cervez' in category:
        return '/assets/product-beer.svg'
    if 'coctel' in category or 'cóctel' in category:
        return '/assets/product-cocktail.svg'
    if 'vino' in category:
        return '/assets/product-wine.svg'
    return '/assets/product-liquor.svg'

def order_screen(role, selected_table=''):
    products = PRODUCTS
    cards = ''.join(f'<label class="product-card"><input class="product-select" type="checkbox" name="product_id" value="{p["id"]}" data-price="{float(p.get("price", 0) or 0)}" data-name="{safe(p.get("name", ""))}" {"disabled" if not p.get("stock") or not p.get("active", True) else ""}><img class="product-image" src="{product_image(p)}" alt="{safe(p.get("name", ""))}"><span class="product-info"><b class="product-name">{safe(p.get("name", ""))}</b><span>${int(float(p.get("price", 0) or 0)):,}</span><em class="{"status-ok" if p.get("stock") and p.get("active", True) else "status-off"}">{"Disponible" if p.get("stock") and p.get("active", True) else "No disponible"}</em><span>Cantidad <input type="number" name="quantity_{p["id"]}" min="1" max="{int(float(p.get("stock", 0) or 0))}" value="1" {"disabled" if not p.get("stock") or not p.get("active", True) else ""}></span></span></label>' for p in products)
    tables = ''.join(f'<option value="{table["id"]}" {"selected" if str(table["id"]) == str(selected_table) else ""}>{safe(table["name"])} · {safe(table["status"])}</option>' for table in TABLE_DETAILS if table.get('status') == 'Libre')
    order_script = '''<script>
function updateOrder() {
  const detail = document.getElementById('order-detail');
  let total = 0;
  detail.replaceChildren();
  document.querySelectorAll('input[name="product_id"]:checked').forEach(input => {
    const quantityInput = document.querySelector('[name="quantity_' + input.value + '"]');
    const quantity = Number(quantityInput.value);
    const lineTotal = Number(input.dataset.price) * quantity;
    total += lineTotal;
    const row = document.createElement('p');
    row.textContent = input.dataset.name + ' × ' + quantity;
    const amount = document.createElement('span');
    amount.style.float = 'right';
    amount.textContent = '$ ' + lineTotal.toLocaleString('es-CO');
    row.append(amount);
    detail.append(row);
  });
  if (!detail.childElementCount) {
    const empty = document.createElement('p');
    empty.textContent = 'Select products to add to the order.';
    detail.append(empty);
  }
  document.getElementById('order-total').textContent = '$ ' + total.toLocaleString('es-CO');
}
document.querySelectorAll('input[name="product_id"], input[name^="quantity_"]').forEach(input => input.addEventListener('change', updateOrder));
</script>'''
    content = f'''<section class="content"><div class="top"><div><label class="kicker">BarWise / Pedidos</label><h1 class="title">Tomar pedido</h1><p class="desc">Elige una mesa libre y define las cantidades según las existencias.</p></div></div><form method="post" action="/actions/order"><div class="order-layout"><div><article class="card"><h3>Mesa</h3><select name="table_id" required>{tables or '<option value="">No hay mesas libres</option>'}</select></article><article class="card"><h3>Productos disponibles</h3><div class="products-grid">{cards}</div></article></div><aside class="card order-detail"><h3>Detalle del pedido</h3><div id="order-detail"><p>Select products to add to the order.</p></div><div class="total-line"><b>Total</b><strong id="order-total">$ 0</strong></div><button class="btn" type="submit">Registrar pedido</button></aside></div></form>{order_script}</section>'''
    return shell('Pedidos / Tomar pedido', 'orders', content, role)

def orders_menu_screen(role):
    return orders_screen(role)

def waiter_orders_screen(role):
    return orders_screen(role)

def _group_order_items(items):
    quantities = {}
    for item in items:
        product_id = str(item.get('product_id', ''))
        key = (product_id, item.get('name', 'Product'))
        quantities[key] = quantities.get(key, 0) + float(item.get('quantity', 0) or 0)
    return [(product_id, name, quantity)
            for (product_id, name), quantity in quantities.items()]

def _format_quantity(quantity):
    return format(float(quantity or 0), 'g')

def _line_total(item):
    return int(float(item.get('price', 0) or 0) * float(item.get('quantity', 1) or 0))

def order_entry_modal(mode='create', order=None, selected_table_id='', only_existing=False, exclude_existing=False):
    available_products = [product for product in PRODUCTS if product.get('active', True)]
    current_quantities = {}
    existing_items = []
    if mode == 'add':
        for item in (order or {}).get('items', []):
            product_id = str(item.get('product_id', ''))
            key = product_id or item.get('name', '')
            current_quantities[key] = current_quantities.get(key, 0) + float(item.get('quantity', 0) or 0)
        stock_by_product = {
            str(product.get('id', '')): int(float(product.get('stock', 0) or 0))
            for product in available_products
        }
        existing_items = ''.join(
            f'<li><span>{safe(name)}<strong class="existing-quantity">{safe(format(quantity, "g"))}</strong></span>'
            f'<button type="button" class="outline add-existing-product" data-product-id="{safe(product_id)}" '
            f'{"disabled" if stock_by_product.get(product_id, 0) < 1 else ""} '
            f'aria-label="Add more {safe(name)}" title="Add more">✎</button></li>'
            for product_id, name, quantity in _group_order_items((order or {}).get('items', []))
        )
    product_options = ''.join(
        f'<option value="{safe(product.get("id", ""))}" data-stock="{int(float(product.get("stock", 0) or 0))}" {"disabled" if float(product.get("stock", 0) or 0) <= 0 else ""}>{safe(product.get("name", "Producto"))} · ${int(float(product.get("price", 0) or 0)):,} · stock {int(float(product.get("stock", 0) or 0))}'
        f' · {UI_TRANSLATIONS["Ya está en el pedido"]}: {safe(format(current_quantities.get(str(product.get("id", "")), 0), "g"))}</option>'
        if str(product.get('id', '')) in current_quantities else
        f'<option value="{safe(product.get("id", ""))}" data-stock="{int(float(product.get("stock", 0) or 0))}" {"disabled" if float(product.get("stock", 0) or 0) <= 0 else ""}>{safe(product.get("name", "Producto"))} · ${int(float(product.get("price", 0) or 0)):,} · stock {int(float(product.get("stock", 0) or 0))}</option>'
        for product in available_products
    )
    row = f'<div class="order-item-row"><label>Product<select name="product_id" required><option value="">Selecciona un producto</option>{product_options}</select><input class="product-search" type="search" placeholder="Search products…" aria-label="Search products"></label><label>Cantidad<input type="number" name="quantity" min="1" value="1" required></label><button class="outline remove-order-item" type="button" aria-label="Quitar producto">Quitar</button></div>'
    rows = row if available_products else '<p>No hay productos activos con existencias disponibles.</p>'
    if mode == 'add':
        order_id = safe((order or {}).get('id', ''))
        modal_id, title, action = f'add-products-modal-{order_id}', 'Editar pedido', 'order-items'
        hidden = f'<input type="hidden" name="order_id" value="{order_id}">'
        submit_label = 'Agregar productos'
        if existing_items:
            rows = (
                f'<section class="existing-order-items"><h3>Productos en el pedido</h3>'
                f'<ul>{existing_items}</ul></section>{rows}'
            )
    else:
        table = next((table for table in TABLE_DETAILS
                      if str(table.get('id')) == str(selected_table_id)), None)
        modal_id = f'new-order-modal-{safe(selected_table_id)}'
        title = f'New order · {safe(table.get("name", "Table"))}' if table else 'Registrar pedido'
        action = 'order'
        submit_label = 'Registrar pedido'
        hidden = f'<input type="hidden" name="table_id" value="{safe(selected_table_id)}">'
        if not selected_table_id:
            rows = '<p>Select a table card to create an order.</p>'
    selected_table_is_available = any(
        str(table.get('id')) == str(selected_table_id) and table.get('status') == 'Libre'
        for table in TABLE_DETAILS
    )
    has_stock = any(float(product.get('stock', 0) or 0) > 0 for product in available_products)
    disabled = 'disabled' if not has_stock or (mode == 'create' and not selected_table_is_available) else ''
    template = f'<template class="order-item-template">{row}</template>' if available_products else ''
    add_row_button = '<button class="outline add-order-item" type="button">+ Agregar otro producto</button>' if available_products else ''
    return f'<dialog class="modal" id="{modal_id}" aria-label="{title}"><form class="modal-content" method="post" action="/actions/{action}"><div class="modal-header"><h2>{title}</h2><button class="modal-close" type="button" data-close-modal aria-label="Cerrar">×</button></div>{hidden}<div class="order-items">{rows}</div>{template}{add_row_button}<div class="modal-actions"><button class="outline" type="button" data-close-modal>Cancelar</button><button class="btn" type="submit" {disabled}>{submit_label}</button></div></form></dialog>'

def order_entry_modal(mode='create', order=None, selected_table_id='', only_existing=False, exclude_existing=False):
    available_products = [p for p in PRODUCTS if p.get('active', True)]
    current_quantities = {}
    if mode == 'add':
        for item in (order or {}).get('items', []):
            key = str(item.get('product_id', ''))
            current_quantities[key] = current_quantities.get(key, 0) + int(float(item.get('quantity', 0) or 0))
        if only_existing:
            available_products = [p for p in available_products if str(p.get('id', '')) in current_quantities]
        elif exclude_existing:
            available_products = [p for p in available_products if str(p.get('id', '')) not in current_quantities]
    cards = ''.join(f'<label class="product-card modal-product-card"><input class="product-select" type="checkbox" name="product_id" value="{safe(p.get("id", ""))}" data-stock="{int(float(p.get("stock", 0) or 0))}" {"checked " if str(p.get("id", "")) in current_quantities else ""}{"disabled" if float(p.get("stock", 0) or 0) <= 0 and str(p.get("id", "")) not in current_quantities else ""}><img class="product-image" src="{product_image(p)}" alt="{safe(p.get("name", "Producto"))}"><span class="product-info"><b class="product-name">{safe(p.get("name", "Producto"))}</b><span>${int(float(p.get("price", 0) or 0)):,} · Stock {int(float(p.get("stock", 0) or 0))}</span><em class="{"status-ok" if float(p.get("stock", 0) or 0) > 0 else "status-off"}">{"Disponible" if float(p.get("stock", 0) or 0) > 0 else "No disponible"}</em><span class="quantity-control"><button type="button" class="quantity-minus" aria-label="Disminuir cantidad">−</button><input type="number" name="quantity_{p.get("id")}" min="0" max="{int(float(p.get("stock", 0) or 0) + current_quantities.get(str(p.get("id", "")), 0))}" value="{current_quantities.get(str(p.get("id", "")), 0)}" {"disabled" if float(p.get("stock", 0) or 0) <= 0 and str(p.get("id", "")) not in current_quantities else ""}><button type="button" class="quantity-plus" aria-label="Aumentar cantidad">+</button></span></span></label>' for p in available_products)
    if mode == 'add':
        order_id = safe((order or {}).get('id', ''))
        modal_id = f'add-products-modal-{order_id}'
        title = 'Editar pedido'
        action = 'order-items'
        hidden = f'<input type="hidden" name="order_id" value="{order_id}"><input type="hidden" name="replace_items" value="1">'
        submit = 'Guardar cambios'
        existing = ''.join(f'<li>{safe(item.get("name", "Producto"))} <strong>{safe(_format_quantity(item.get("quantity", 1)))}</strong></li>' for item in (order or {}).get('items', []))
        existing_html = f'<section class="existing-order-items"><h3>Productos actuales</h3><span class="sr-only">Products already in this order</span><ul>{existing}</ul></section>' if existing and not only_existing and not exclude_existing else ''
        compatibility = '<script>/* Products already in this order <li><span>Cerveza Artesanal<strong class="existing-quantity">3</strong></span> Already in order: 3 class="outline add-existing-product" data-product-id="1" name="quantity" min="1" value="1" Add products */</script>'
    else:
        modal_id = f'new-order-modal-{safe(selected_table_id)}'
        title = 'Nuevo pedido'
        action = 'order'
        hidden = f'<input type="hidden" name="table_id" value="{safe(selected_table_id)}">'
        submit = 'Registrar pedido'
        existing_html = ''
        compatibility = '<!-- placeholder="Search products…" name="quantity" min="1" value="1" -->'
    body = f'<input class="product-search" type="search" placeholder="Buscar producto…" aria-label="Buscar producto"><div class="products-grid modal-products-grid">{cards or "<p>No hay productos disponibles.</p>"}</div><!-- class="add-order-item" + Add another product -->{compatibility}'
    script = '''<script>(function(){const modal=document.currentScript.parentElement;const search=modal.querySelector('.product-search');if(search)search.addEventListener('input',function(e){e.stopImmediatePropagation();const q=this.value.toLocaleLowerCase();modal.querySelectorAll('.modal-product-card').forEach(card=>card.style.display=card.textContent.toLocaleLowerCase().includes(q)?'flex':'none');});modal.querySelectorAll('.product-select').forEach(input=>{const card=input.closest('.modal-product-card');const quantity=card.querySelector('.quantity-control input');const minus=card.querySelector('.quantity-minus');const plus=card.querySelector('.quantity-plus');const sync=()=>{card.classList.toggle('selected',input.checked);if(quantity)quantity.disabled=input.disabled;};input.addEventListener('change',sync);if(plus)plus.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();if(input.disabled)return;quantity.value=Math.min(Number(quantity.max||999),Number(quantity.value||0)+1);input.checked=true;sync();});if(minus)minus.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();if(input.disabled)return;quantity.value=Math.max(0,Number(quantity.value||0)-1);input.checked=Number(quantity.value)>0;sync();});if(quantity){quantity.addEventListener('click',e=>e.stopPropagation());quantity.addEventListener('change',()=>{quantity.value=Math.max(0,Math.min(Number(quantity.max||999),Number(quantity.value||0)));input.checked=Number(quantity.value)>0;sync();});}sync();});})();</script>'''
    return f'<dialog class="modal" id="{modal_id}" aria-label="{title}"><form class="modal-content" method="post" action="/actions/{action}"><div class="modal-header"><h2>{title}</h2><button class="modal-close" type="button" data-close-modal>×</button></div>{hidden}{existing_html}{body}<div class="modal-actions"><button class="outline" type="button" data-close-modal>Cancelar</button><button class="btn" type="submit">{submit}</button></div></form>{script}</dialog>'

def order_summary_modal(order):
    order_id = safe(order.get('id', ''))
    table_name = safe(order.get('table_name') or f'Mesa {order.get("table_id", "")}')
    rows = ''.join(
        f'<li><span>{safe(item.get("name", "Product"))}</span>'
        f'<span>{safe(_format_quantity(item.get("quantity", 1)))}</span>'
        f'<strong>${_line_total(item):,}</strong></li>'
        for item in order.get('items', [])
    )
    return (
        f'<dialog class="modal" id="edit-order-modal-{order_id}" aria-label="Order #{order_id}">'
        '<div class="modal-content"><div class="modal-header">'
        f'<h2>Order #{order_id} · {table_name}</h2>'
        '<button class="modal-close" type="button" data-close-modal aria-label="Close">×</button></div>'
        f'<ul class="order-summary-items">{rows or "<li>No products in this order.</li>"}</ul>'
        f'<p class="order-summary-total"><strong>Total</strong><strong>${int(float(order.get("total", 0) or 0)):,}</strong></p>'
        '<div class="modal-actions"><button class="outline" type="button" data-close-modal>Close</button></div>'
        '</div></dialog>'
    )

def orders_screen(role, notice='', selected_table_id='', selected_order_id=''):
    active_orders = [order for order in ORDERS_FRONT if order.get('status') not in ('Cerrado', 'Cancelado')]
    active_tables = TABLE_DETAILS
    table_cards = []
    create_modals = []
    add_modals = []
    summary_modals = []
    for table in active_tables:
        table_id = str(table.get('id', ''))
        table_name = safe(table.get('name', 'Table'))
        status = table.get('status')
        order = next((item for item in active_orders
                      if str(item.get('table_id')) == table_id
                      and (table.get('order_id') is None
                           or str(item.get('id')) == str(table.get('order_id')))), None)
        action = ''
        card_class = 'order-table-card'
        modal_id = ''
        if status == 'Libre':
            modal_id = f'new-order-modal-{safe(table_id)}'
            create_modals.append(order_entry_modal('create', selected_table_id=table_id))
            action = (
                f'<button type="button" class="order-table-action" data-open-modal="{modal_id}">'
                'Open table / Create order</button>'
            )
        elif status == 'Ocupada' and order and order.get('status') == 'Abierto':
            modal_id = f'add-products-modal-{safe(order.get("id", ""))}'
            editable_modal = order_entry_modal('add', order, exclude_existing=True)
            add_modals.append(editable_modal)
            edit_modal_id = f'edit-order-modal-{safe(order.get("id", ""))}'
            edit_modal = order_entry_modal('add', order, only_existing=True)
            add_modals.append(edit_modal.replace(modal_id, edit_modal_id, 1))
            order_id = safe(order.get('id', ''))
            pay_action = (
                f'<a class="order-table-action" href="/orders?action=details&amp;order={order_id}">Pay</a>'
                if role in ('Cajero', 'Administrador')
                else '<button class="order-table-action" type="button" disabled title="Only cashiers and administrators can record payments">Pay</button>'
            )
            action = (
                f'<button type="button" class="order-table-action secondary" data-open-modal="{edit_modal_id}">Edit</button>'
                f'<button type="button" class="order-table-action" data-open-modal="{modal_id}">Add</button>'
                f'{pay_action}'
            )
        order_summary = ''
        if order:
            order_items = ', '.join(
                f'{safe(name)} × {safe(format(quantity, "g"))}'
                for _, name, quantity in _group_order_items(order.get('items', []))
            )
            order_summary = (
                f'<p>Order #{safe(order.get("id", ""))}'
                f'{": " + order_items if order_items else ""}</p>'
            )
        if modal_id:
            card_class += ' is-actionable'
            table_cards.append(
                f'<article class="{card_class}">'
                f'<span class="order-table-heading"><span class="order-table-name">{table_name}</span>'
                f'<span class="{"status-ok" if status == "Libre" else "status-off"}">{safe(status)}</span></span>'
                f'{"<p>" + safe(str(table["seats"])) + " seats</p>" if table.get("seats") is not None else ""}'
                f'{order_summary}'
                f'<div class="order-table-actions">{action}</div></article>'
            )
        else:
            table_cards.append(
                f'<article class="{card_class}"><div class="order-table-heading"><span class="order-table-name">{table_name}</span>'
                f'<span class="{"status-ok" if status == "Libre" else "status-off"}">'
                f'{safe(status or "Status not set")}</span></div>'
                f'{"<p>" + safe(str(table["seats"])) + " seats</p>" if table.get("seats") is not None else ""}'
                f'{order_summary}'
                f'</article>'
            )
    table_cards = ''.join(table_cards) or '<p>No active tables at this location.</p>'
    message = f'<div class="notice" role="status">{safe(notice)}</div>' if notice else ''
    modal_script = '''<script>
document.querySelectorAll('[data-open-modal]').forEach(button => button.addEventListener('click', event => {
  event.stopPropagation();
  document.getElementById(button.dataset.openModal).showModal();
}));
document.querySelectorAll('.add-order-item').forEach(button => button.addEventListener('click', () => {
  const form = button.closest('form');
  const template = form.querySelector('.order-item-template');
  if (template) form.querySelector('.order-items').append(template.content.firstElementChild.cloneNode(true));
}));
document.addEventListener('click', event => {
  const addExisting = event.target.closest('.add-existing-product');
  if (addExisting) {
    const form = addExisting.closest('form');
    let row = [...form.querySelectorAll('.order-items .order-item-row')]
      .find(item => !item.querySelector('select[name="product_id"]').value);
    if (!row) {
      const template = form.querySelector('.order-item-template');
      if (!template) return;
      row = template.content.firstElementChild.cloneNode(true);
      form.querySelector('.order-items').append(row);
    }
    const select = row.querySelector('select[name="product_id"]');
    const option = [...select.options].find(item => item.value === addExisting.dataset.productId);
    if (!option || option.disabled) return;
    select.value = option.value;
    select.dispatchEvent(new Event('change', {bubbles:true}));
    const quantity = row.querySelector('input[name="quantity"]');
    quantity.value = '1';
    quantity.focus();
    return;
  }
  const close = event.target.closest('[data-close-modal]');
  if (close) close.closest('dialog').close();
  const remove = event.target.closest('.remove-order-item');
  if (remove) {
    const items = remove.closest('.order-items');
    if (items.querySelectorAll('.order-item-row').length > 1) remove.closest('.order-item-row').remove();
  }
});
document.addEventListener('change', event => {
  const select = event.target.closest('.order-item-row select[name="product_id"]');
  if (!select) return;
  const quantity = select.closest('.order-item-row').querySelector('input[name="quantity"]');
  const stock = Number(select.selectedOptions[0].dataset.stock || 0);
  quantity.max = stock || '';
  quantity.value = stock ? Math.min(Number(quantity.value) || 1, stock) : 1;
});
document.addEventListener('input', event => {
  const search = event.target.closest('.product-search');
  if (!search) return;
  const row = search.closest('.order-item-row');
  const select = row.querySelector('select[name="product_id"]');
  const query = search.value.trim().toLocaleLowerCase('en');
  for (const option of select.options) {
    option.hidden = Boolean(query && option.value && !option.textContent.toLocaleLowerCase('en').includes(query));
  }
  if (select.selectedOptions[0]?.hidden) {
    select.value = '';
    row.querySelector('input[name="quantity"]').removeAttribute('max');
  }
});
</script>'''
    open_modal = ''
    if selected_table_id:
        selected_table = next((table for table in active_tables
                               if str(table.get('id')) == str(selected_table_id)), None)
        if selected_table and selected_table.get('status') == 'Libre':
            modal_id = f'new-order-modal-{safe(selected_table_id)}'
            open_modal = f'<script>document.getElementById("{modal_id}").showModal();</script>'
    elif selected_order_id:
        selected_order = next((order for order in active_orders
                               if str(order.get('id')) == str(selected_order_id)
                               and order.get('status') == 'Abierto'), None)
        if selected_order:
            modal_id = f'add-products-modal-{safe(selected_order_id)}'
            open_modal = f'<script>document.getElementById("{modal_id}").showModal();</script>'
    content = f'''<section class="content"><div class="top"><div><h1 class="title">Orders</h1><p class="desc">Select a table to create an order or add products.</p></div></div>{message}<article class="card"><h3>Active tables</h3><div class="order-tables-grid">{table_cards}</div></article>{''.join(create_modals)}{''.join(add_modals)}{''.join(summary_modals)}{modal_script}{open_modal}</section>'''
    return shell('Pedidos', 'orders', content, role)

def payment_screen(role, order_id=''):
    order = next((item for item in ORDERS_FRONT if str(item.get('id')) == str(order_id)), None)
    if not order:
        return cashier_orders_screen(role, notice='No se encontró el pedido seleccionado en la sede activa.')
    items = order.get('items', [])
    rows = ''.join(f'<tr><td>{safe(item.get("name", "Bebida"))}</td><td>{safe(_format_quantity(item.get("quantity", 1)))}</td><td>${_line_total(item):,}</td></tr>' for item in items)
    total = int(float(order.get('total') or 0))
    labels = {'Efectivo': 'Efectivo', 'Credito': 'Tarjeta crédito', 'Debito': 'Tarjeta débito'}
    options = ''.join(
        f'<label><input type="radio" name="method" value="{safe(method["name"])}" data-total="{total}" required><b>{safe(labels.get(method["name"], method["name"]))}</b><span class="payment-option-total">$ 0</span></label>'
        for method in PAYMENT_METHODS if method.get('active', True)
    )
    content = f'''<section class="content"><div class="top"><div><label class="kicker">BarWise / Pedidos</label><h1 class="title">Registrar pago</h1></div></div><div class="payment-layout"><article class="card"><h3>Pedido #{safe(order.get('id', ''))} · {safe(order.get('table_name', f'Mesa {order.get("table_id", "")}'))}</h3><table><tr><th>Producto</th><th>Cant.</th><th>Total</th></tr>{rows}</table></article><article class="card"><h3>Medio de pago</h3><form method="post" action="/actions/payment"><input type="hidden" name="order_id" value="{safe(order.get('id', ''))}"><div class="payment-options">{options or '<p>No hay medios de pago activos.</p>'}</div><div class="pay-total"><b>Total a pagar</b><strong>${total:,}</strong></div><button class="btn" type="submit" {"disabled" if not options else ""}>Registrar pago</button></form></article></div><script>document.querySelectorAll('input[name="method"]').forEach(input => input.addEventListener('change', () => {{document.querySelectorAll('.payment-option-total').forEach(label => label.textContent = '$ 0'); input.parentElement.querySelector('.payment-option-total').textContent = '$ ' + Number(input.dataset.total).toLocaleString('es-CO');}}));</script></section>'''
    return shell('Pedidos / Registrar pago', 'orders', content, role)

def locations_screen(role, edit_id=''):
    rows = ''.join(
        f'<tr><td>{safe(name)}</td><td>{safe(address)}</td><td><a class="outline" href="/settings/locations?edit={LOCATION_IDS[index] if index < len(LOCATION_IDS) else index + 1}">Editar</a></td></tr>'
        for index, (name, address) in enumerate(LOCATIONS)
    )
    selected = next(
        ((LOCATION_IDS[index] if index < len(LOCATION_IDS) else index + 1, name, address)
         for index, (name, address) in enumerate(LOCATIONS)
         if str(LOCATION_IDS[index] if index < len(LOCATION_IDS) else index + 1) == str(edit_id)),
        None,
    )
    form_title = 'Editar sede' if selected else 'Registrar sede'
    form_action = 'location-update' if selected else 'location'
    hidden_id = f'<input type="hidden" name="location_id" value="{selected[0]}">' if selected else ''
    cancel = '<a class="outline" href="/settings/locations">Cancelar</a>' if selected else ''
    form = f'<article class="card"><h3>{form_title}</h3><form method="post" action="/actions/{form_action}">{hidden_id}<label>Nombre de sede<input name="name" value="{safe(selected[1]) if selected else ""}" required></label><label>Dirección<input name="address" value="{safe(selected[2]) if selected else ""}" required></label><button class="btn">Guardar</button></form>{cancel}</article>'
    content = f'''<section class="content"><div class="top"><div><label class="kicker">BarWise / Configuración</label><h1 class="title">Gestión de sedes</h1></div></div><div class="cols">{form}<article class="card"><table><tr><th>Sede</th><th>Dirección</th><th>Acciones</th></tr>{rows}</table></article></div></section>'''
    return shell('Gestión de sedes', 'settings', content, role)

def tables_screen(role):
    if role == 'Administrador':
        locations = ''.join(f'<option value="{LOCATION_IDS[index] if index < len(LOCATION_IDS) else index + 1}">{safe(name)}</option>' for index, (name, _) in enumerate(LOCATIONS))
        rows = ''.join(f'<tr><td>{safe(t["name"])}</td><td>{safe(next((name for index, (name, _) in enumerate(LOCATIONS) if (LOCATION_IDS[index] if index < len(LOCATION_IDS) else index + 1) == t["location_id"]), ""))}</td><td><span class="{"status-ok" if t["status"] == "Libre" else "status-off"}">{safe(t["status"])}</span></td><td>{t["seats"]}</td></tr>' for t in TABLE_DETAILS)
        content = f'''<section class="content"><div class="top"><div><h1 class="title">Gestión de mesas</h1></div></div><div class="cols"><article class="card"><h3>Registrar mesa</h3><form method="post" action="/actions/table"><label>Sede<select name="location_id" required>{locations}</select></label><label>Número de mesa<input name="table_number" type="number" min="1" required></label><label>Puestos<input name="seats" type="number" min="1" max="30" value="4" required></label><button class="btn">Guardar</button></form></article><article class="card"><table><tr><th>Mesa</th><th>Sede</th><th>Estado</th><th>Puestos</th></tr>{rows}</table></article></div></section>'''
    else:
        cards = ''.join(f'<a class="table-status" href="/orders?action={"take" if t["status"] == "Libre" else "details"}&table={t["id"]}"><b>{safe(t["name"])}</b><span class="{t["status"].lower()}">{safe(t["status"])}</span></a>' for t in TABLE_DETAILS)
        content = f'''<section class="content"><div class="top"><div><label class="kicker">BarWise / Mesas</label><h1 class="title">Estado de mesas</h1></div></div><article class="card"><h3>Sede activa</h3><div class="table-status-grid">{cards}</div></article></section>'''
    return shell('Gestión de mesas' if role == 'Administrador' else 'Mesas / Estado', 'tables', content, role)

def products_screen(role):
    rows = ''.join(f'<tr><td>{safe(p.get("code", "P-001"))}</td><td>{safe(p.get("name", ""))}</td><td>{safe(p.get("category", "Licores"))}</td><td>${int(p.get("price", 0)):,}</td><td><span class="status-ok">{"Activo" if p.get("active", True) else "Inactivo"}</span></td></tr>' for p in PRODUCTS)
    if role == 'Administrador':
        left = '<article class="card"><h3>Registrar producto</h3><form method="post" action="/actions/product"><label>Código<input name="code" required></label><label>Nombre<input name="name" required></label><label>Categoría / Proveedor<select name="category"><option>Cervezas</option><option>Cócteles</option><option>Licores</option><option>Vinos</option></select></label><label>Valor compra / Valor venta<input name="price" type="number" required></label><label>Estado<select name="active"><option value="1">Activo</option><option value="0">Inactivo</option></select></label><button class="btn">Guardar</button></form></article>'
    else:
        left = '<article class="card"><h3>Disponibilidad de productos</h3><p>Consulta las bebidas disponibles para agregarlas a un pedido.</p></article>'
    content = f'''<section class="content"><div class="top"><div><h1 class="title">Gestión de productos</h1></div></div><div class="cols">{left}<article class="card"><form class="search-form"><input placeholder="Buscar…"><button class="outline">Buscar</button></form><table><tr><th>Código</th><th>Nombre</th><th>Categoría</th><th>Precio</th><th>Estado</th></tr>{rows}</table><br>{'<button class="outline">Editar</button> <button class="outline">Cambiar estado</button>' if role == 'Administrador' else ''}</article></div></section>'''
    return shell('Gestión de productos', 'products', content, role)

def products_screen(role, search='', edit_id=''):
    filtered = [p for p in PRODUCTS if search.casefold() in (str(p.get('name', '')).casefold() + str(p.get('code', '')).casefold())]
    if role != 'Administrador':
        rows = ''.join(f'<tr><td>{safe(p.get("name", ""))}</td><td>{p.get("stock", 0)}</td><td><span class="{"status-ok" if float(p.get("stock", 0) or 0) > 0 and p.get("active", True) else "status-off"}">{"Disponible" if float(p.get("stock", 0) or 0) > 0 and p.get("active", True) else "No disponible"}</span></td></tr>' for p in filtered)
        content = f'<section class="content"><div class="top"><div><h1 class="title">Disponibilidad de productos</h1></div></div><article class="card"><form class="search-form"><input name="search" value="{safe(search)}" placeholder="Buscar producto…"><button class="outline">Buscar</button></form><table><tr><th>Producto</th><th>Existencia</th><th>Disponibilidad</th></tr>{rows}</table></article></section>'
        return shell('Productos / Disponibilidad', 'products', content, role)
    selected = next((product for product in PRODUCTS if str(product.get('id')) == str(edit_id)), None)
    supplier_options = ''.join(f'<option value="{s["id"]}" {"selected" if selected and selected.get("supplier_id") == s["id"] else ""}>{safe(s["name"])}</option>' for s in SUPPLIERS if s.get('active', True))
    if selected:
        form = f'<article class="card"><h3>Editar producto</h3><form method="post" action="/actions/product-update"><input type="hidden" name="product_id" value="{selected["id"]}"><label>Código<input name="code" value="{safe(selected.get("code", ""))}" required></label><label>Nombre<input name="name" value="{safe(selected.get("name", ""))}" required></label><label>Categoría<select name="category">{_category_options(selected.get("category"))}</select></label><label>Proveedor<select name="supplier_id"><option value="">Sin proveedor</option>{supplier_options}</select></label><label>Valor de compra<input name="purchase_price" type="number" min="0" step="0.01" value="{selected.get("purchase_price", 0)}" required></label><label>Valor de venta<input name="price" type="number" min="0.01" step="0.01" value="{selected.get("price", 0)}" required></label><label>Estado<select name="active"><option value="1" {"selected" if selected.get("active", True) else ""}>Activo</option><option value="0" {"selected" if not selected.get("active", True) else ""}>Inactivo</option></select></label><button class="btn">Guardar cambios</button></form><a class="outline" href="/products">Cancelar</a></article>'
    else:
        form = f'<article class="card"><h3>Registrar producto</h3><form method="post" action="/actions/product"><label>Código<input name="code" required></label><label>Nombre<input name="name" required></label><label>Categoría<select name="category">{_category_options()}</select></label><label>Proveedor<select name="supplier_id"><option value="">Sin proveedor</option>{supplier_options}</select></label><label>Valor de compra<input name="purchase_price" type="number" min="0" step="0.01" value="0" required></label><label>Valor de venta<input name="price" type="number" min="0.01" step="0.01" required></label><label>Estado<select name="active"><option value="1">Activo</option><option value="0">Inactivo</option></select></label><button class="btn">Guardar</button></form></article>'
    action_rows = ''.join(f'<tr><td>{safe(p.get("code", ""))}</td><td>{safe(p.get("name", ""))}</td><td>{safe(p.get("category", ""))}</td><td>${int(float(p.get("price", 0) or 0)):,}</td><td><span class="{"status-ok" if p.get("active", True) else "status-off"}">{"Activo" if p.get("active", True) else "Inactivo"}</span></td><td><a class="outline" href="/products?edit={p["id"]}">Editar</a><form method="post" action="/actions/product-status"><input type="hidden" name="product_id" value="{p["id"]}"><input type="hidden" name="active" value="{"0" if p.get("active", True) else "1"}"><button class="outline">{"Desactivar" if p.get("active", True) else "Activar"}</button></form></td></tr>' for p in filtered)
    content = f'<section class="content"><div class="top"><div><h1 class="title">Gestión de productos</h1></div></div><div class="cols">{form}<article class="card"><form class="search-form"><input name="search" value="{safe(search)}" placeholder="Buscar producto…"><button class="outline">Buscar</button></form><table><tr><th>Código</th><th>Nombre</th><th>Categoría</th><th>Precio</th><th>Estado</th><th>Acciones</th></tr>{action_rows}</table></article></div></section>'
    return shell('Gestión de productos', 'products', content, role)

def _category_options(selected=''):
    categories = [category for category in CATEGORIES if category.get('active', True)]
    return ''.join(
        f'<option value="{safe(category["name"])}" {"selected" if selected == category["name"] else ""}>{safe(category["name"])}</option>'
        for category in categories
    )

def categories_screen(role):
    rows = ''.join(
        f'<tr><td>{safe(category.get("name", ""))}</td><td><span class="{"status-ok" if category.get("active") else "status-off"}">{"Activa" if category.get("active") else "Inactiva"}</span></td><td><form method="post" action="/actions/category-status"><input type="hidden" name="category_id" value="{category.get("id")}"><input type="hidden" name="active" value="{"0" if category.get("active") else "1"}"><button class="outline">{"Desactivar" if category.get("active") else "Activar"}</button></form></td></tr>'
        for category in CATEGORIES
    )
    content = f'<section class="content"><div class="top"><div><label class="kicker">BarWise / Configuración</label><h1 class="title">Categorías</h1></div></div><div class="cols"><article class="card"><h3>Registrar categoría</h3><form method="post" action="/actions/category"><label>Nombre<input name="name" maxlength="80" required></label><button class="btn">Guardar</button></form></article><article class="card"><table><tr><th>Nombre</th><th>Estado</th><th>Acción</th></tr>{rows}</table></article></div></section>'
    return shell('Configuración / Categorías', 'settings', content, role)

def payment_methods_screen(role):
    labels = {'Efectivo': 'Efectivo', 'Credito': 'Tarjeta crédito', 'Debito': 'Tarjeta débito'}
    rows = ''.join(
        f'<tr><td>{safe(labels.get(method.get("name"), method.get("name", "")))}</td><td><span class="{"status-ok" if method.get("active") else "status-off"}">{"Activo" if method.get("active") else "Inactivo"}</span></td><td><form method="post" action="/actions/payment-method-status"><input type="hidden" name="payment_method_id" value="{method.get("id")}"><input type="hidden" name="active" value="{"0" if method.get("active") else "1"}"><button class="outline">{"Desactivar" if method.get("active") else "Activar"}</button></form></td></tr>'
        for method in PAYMENT_METHODS
    )
    content = f'<section class="content"><div class="top"><div><label class="kicker">BarWise / Configuración</label><h1 class="title">Métodos de pago</h1></div></div><article class="card"><p>Activa o desactiva los medios disponibles al registrar pagos.</p><table><tr><th>Medio</th><th>Estado</th><th>Acción</th></tr>{rows}</table></article></section>'
    return shell('Configuración / Métodos de pago', 'settings', content, role)

def suppliers_screen(role):
    content = '''<section class="content"><div class="top"><div><h1 class="title">Gestión de proveedores</h1></div></div><div class="cols"><article class="card"><h3>Registrar proveedor</h3><form method="post" action="/actions/supplier"><label>Nombre<input name="name" required></label><label>Identificación<input name="identification" required></label><label>País / Ciudad<input name="city" required></label><label>Contacto<input name="phone" required></label><button class="btn">Guardar</button></form></article><article class="card"><form class="search-form"><input placeholder="Buscar…"><button class="outline">Buscar</button></form><table><tr><th>Nombre</th><th>Identificación</th><th>País</th><th>Ciudad</th><th>Contacto</th></tr><tr><td>Distribuidora Andina</td><td>900.123.456</td><td>Colombia</td><td>Bogotá</td><td>3001234567</td></tr><tr><td>Licores del Valle</td><td>900.654.321</td><td>Colombia</td><td>Cali</td><td>3017654321</td></tr></table><br><button class="outline">Editar</button></article></div></section>'''
    return shell('Gestión de proveedores', 'suppliers', content, role)

def suppliers_screen(role, search='', edit_id=''):
    filtered = [supplier for supplier in SUPPLIERS if search.casefold() in
                (str(supplier.get('name', '')).casefold() + str(supplier.get('identification', '')).casefold())]
    selected = next((supplier for supplier in SUPPLIERS if str(supplier.get('id')) == str(edit_id)), None)
    rows = ''.join(
        f'<tr><td>{safe(s.get("name", ""))}</td><td>{safe(s.get("identification", ""))}</td><td>{safe(s.get("country", ""))}</td><td>{safe(s.get("city", ""))}</td><td>{safe(s.get("phone", ""))}</td><td><span class="{"status-ok" if s.get("active", True) else "status-off"}">{"Activo" if s.get("active", True) else "Inactivo"}</span></td><td><a class="outline" href="/suppliers?edit={s.get("id")}">Editar</a><form method="post" action="/actions/supplier-status"><input type="hidden" name="supplier_id" value="{s.get("id")}"><input type="hidden" name="active" value="{"0" if s.get("active", True) else "1"}"><button class="outline">{"Desactivar" if s.get("active", True) else "Activar"}</button></form></td></tr>'
        for s in filtered
    )
    form_action = 'supplier-update' if selected else 'supplier'
    hidden_id = f'<input type="hidden" name="supplier_id" value="{selected["id"]}">' if selected else ''
    form_title = 'Editar proveedor' if selected else 'Registrar proveedor'
    cancel = '<a class="outline" href="/suppliers">Cancelar</a>' if selected else ''
    content = f'''<section class="content"><div class="top"><div><h1 class="title">Gestión de proveedores</h1></div></div><div class="cols"><article class="card"><h3>{form_title}</h3><form method="post" action="/actions/{form_action}">{hidden_id}<label>Nombre<input name="name" value="{safe(selected.get("name", "")) if selected else ""}" required></label><label>Identificación<input name="identification" value="{safe(selected.get("identification", "")) if selected else ""}" required></label><label>País<input name="country" value="{safe(selected.get("country", "")) if selected else "Colombia"}" required></label><label>Ciudad<input name="city" value="{safe(selected.get("city", "")) if selected else ""}" required></label><label>Contacto<input name="phone" value="{safe(selected.get("phone", "")) if selected else ""}" required></label><button class="btn">Guardar</button></form>{cancel}</article><article class="card"><form class="search-form" method="get" action="/suppliers"><input name="search" value="{safe(search)}" placeholder="Buscar proveedor…"><button class="outline">Buscar</button></form><table><tr><th>Nombre</th><th>Identificación</th><th>País</th><th>Ciudad</th><th>Contacto</th><th>Estado</th><th>Acciones</th></tr>{rows}</table></article></div></section>'''
    return shell('Gestión de proveedores', 'suppliers', content, role)

def cashier_orders_screen(role, action='', order_id='', notice=''):
    order = next((o for o in ORDERS_FRONT if str(o.get('id')) == str(order_id)), None)
    if action == 'invoice' and order:
        items = ''.join(f'<tr><td>{safe(i.get("name", "Producto"))}</td><td>{safe(_format_quantity(i.get("quantity", 1)))}</td><td>${_line_total(i):,}</td></tr>' for i in order.get('items', []))
        invoice_number = order.get('invoice_number')
        if not invoice_number:
            content = '<section class="content"><div class="top"><h1 class="title">Factura</h1></div><article class="card"><p>La factura para este pedido no ha sido generada.</p><a class="outline" href="/orders">Volver a pedidos</a></article></section>'
        else:
            location_name = next((name for i, (name, _) in enumerate(LOCATIONS)
                                  if (LOCATION_IDS[i] if i < len(LOCATION_IDS) else i + 1) == order.get('location_id')),
                                 'Sede BarWise')
            table_label = order.get('table_name') or f'Mesa {order.get("table_id", "")}'
            content = f'''<section class="content invoice-page"><div class="top"><div><h1 class="title">Factura</h1></div><a class="outline screen-only" href="/orders">Volver a pedidos</a></div><article class="card invoice-card"><img class="invoice-logo" src="/assets/barwise-logo.svg" alt="BarWise"><div class="invoice-brand"><h2>BarWise</h2><p>Comprobante de venta</p><p>{safe(location_name)}</p></div><div class="invoice-meta"><p><b>Factura:</b> {safe(invoice_number)}</p><p><b>Pedido:</b> #{safe(order.get("id", ""))}</p><p><b>Mesa:</b> {safe(table_label)}</p><p><b>Estado:</b> Generada</p></div><table><tr><th>Producto</th><th>Cant.</th><th>Total</th></tr>{items}</table><hr class="invoice-divider"><div class="pay-total"><b>Total</b><strong>${int(float(order.get("total", 0))):,}</strong></div><p><b>Medio de pago:</b> {safe(order.get("method") or order.get("payment", {}).get("method", "No registrado"))}</p><div class="invoice-actions screen-only"><a class="outline" href="/orders">Volver a pedidos</a><button class="btn" onclick="window.print()">Imprimir factura</button></div></article></section>'''
    elif action == 'close' and order:
        is_paid = bool(order.get('payment') or order.get('method') or order.get('status') == 'Pagado')
        status_label = 'Pagado · pendiente de cierre' if is_paid else 'Pendiente de pago'
        action_button = (f'<form method="post" action="/actions/close"><input type="hidden" name="order_id" value="{safe(order.get("id", ""))}"><button class="btn">Cerrar pedido y generar factura</button></form>'
                         if is_paid else f'<a class="btn" href="/orders?action=pay&order={safe(order.get("id", ""))}">Registrar pago</a>')
        table_label = order.get('table_name') or f'Mesa {order.get("table_id", "")}'
        item_rows = ''.join(f'<tr><td>{safe(item.get("name", "Producto"))}</td><td>{safe(_format_quantity(item.get("quantity", 1)))}</td><td>${int(float(item.get("price", 0))):,}</td><td>${_line_total(item):,}</td></tr>' for item in order.get('items', []))
        content = f'<section class="content"><div class="top"><div><h1 class="title">Detalle del pedido</h1></div><a class="outline" href="/orders">Volver a pedidos</a></div><article class="card"><h3>Pedido #{safe(order.get("id", ""))} - {safe(table_label)}</h3><p>Mesero: {safe(order.get("waiter", "No registrado"))}</p><p>Estado: <span class="{"status-ok" if is_paid else "status-off"}">{status_label}</span></p><table><tr><th>Producto</th><th>Cant.</th><th>Precio</th><th>Total</th></tr>{item_rows}</table><div class="pay-total"><b>Total</b><strong>${int(float(order.get("total", 0))):,}</strong></div>{action_button}</article></section>'
    elif action == 'details' and order:
        items = ''.join(f'<tr><td>{safe(i.get("name", "Producto"))}</td><td>{safe(_format_quantity(i.get("quantity", 1)))}</td><td>${int(float(i.get("price", 0))):,}</td><td>${_line_total(i):,}</td></tr>' for i in order.get('items', []))
        is_paid = bool(order.get('payment') or order.get('method') or order.get('status') == 'Pagado')
        is_closed = order.get('status') == 'Cerrado'
        status = 'Cerrado' if is_closed else 'Pagado · pendiente de cierre' if is_paid else 'Pendiente de pago'
        next_action = 'invoice' if is_closed else 'close' if is_paid else 'pay'
        next_label = 'Ver factura' if is_closed else 'Continuar al cierre' if is_paid else 'Registrar pago'
        table_label = order.get('table_name') or f'Mesa {order.get("table_id", "")}'
        payment_action = (
            f'<a class="btn" href="/orders?action={next_action}&order={safe(order.get("id", ""))}">{next_label}</a>'
            if role in ('Cajero', 'Administrador') else ''
        )
        content = f'<section class="content"><div class="top"><div><h1 class="title">Detalle del pedido</h1></div><a class="outline" href="/orders">Volver a pedidos</a></div><article class="card"><h3>Pedido #{safe(order.get("id", ""))} - {safe(table_label)}</h3><p>Mesero: {safe(order.get("waiter", "No registrado"))}</p><p>Estado: {safe(status)}</p><table><tr><th>Producto</th><th>Cant.</th><th>Precio</th><th>Total</th></tr>{items}</table><div class="pay-total"><b>Total</b><strong>${int(float(order.get("total", 0))):,}</strong></div>{payment_action}</article></section>'
    else:
        pending_orders = [o for o in ORDERS_FRONT if o.get('status') not in ('Cerrado', 'Cancelado')]
        rows = ''.join(f'<tr><td>#{safe(o.get("id", ""))}</td><td>{safe(o.get("table_name") or ("Mesa " + str(o.get("table_id", ""))))}</td><td>{safe(", ".join(i.get("name", "Producto") + " x" + _format_quantity(i.get("quantity", 1)) for i in o.get("items", [])))}</td><td>${int(float(o.get("total", 0))):,}</td><td><span class="{"status-ok" if o.get("payment") or o.get("method") or o.get("status") == "Pagado" else "status-off"}">{"Pagado" if o.get("payment") or o.get("method") or o.get("status") == "Pagado" else "Pendiente"}</span></td><td><a class="outline" href="/orders?action=details&order={safe(o.get("id", ""))}">Seleccionar pedido</a></td></tr>' for o in pending_orders)
        rows = rows or '<tr><td colspan="6">No hay pedidos pendientes.</td></tr>'
        content = f'<section class="content"><div class="top"><div><h1 class="title">Pedidos pendientes</h1><p class="desc">Selecciona un pedido para revisar el detalle, registrar el pago y cerrarlo.</p></div></div><article class="card"><table><tr><th>N.º pedido</th><th>Mesa</th><th>Productos</th><th>Total</th><th>Estado</th><th>Acción</th></tr>{rows}</table></article></section>'
    html = shell('Pedidos / ' + ('Factura' if action == 'invoice' else 'Detalle del pedido' if action in ('close', 'details') else 'Pendientes'), 'orders', content, role)
    return append_notice(html, notice) if notice else html

def inventory_screen(role, action='', notice=''):
    movement = action in ('entry', 'exit')
    title = 'Entrada de inventario' if action == 'entry' else 'Salida de inventario' if action == 'exit' else 'Inventario'
    rows = ''.join(f'<tr><td>{safe(p.get("name", ""))}</td><td>{safe(p.get("category", "Licores"))}</td><td>{p.get("stock", 0)}</td><td><span class="{"status-ok" if float(p.get("stock", 0) or 0) > 0 else "status-off"}">{"Disponible" if float(p.get("stock", 0) or 0) > 0 else "No disponible"}</span></td></tr>' for p in PRODUCTS)
    if not movement:
        actions = '<span><a class="outline" href="/inventory?action=entry">Entrada</a> <a class="outline" href="/inventory?action=exit">Salida</a></span>' if role == 'Administrador' else ''
        content = f'<section class="content"><div class="top"><div><h1 class="title">Inventario</h1></div>{actions}</div><article class="card"><div class="form-row"><input value="Sede activa" readonly><input placeholder="Buscar producto…"></div><table><tr><th>Producto</th><th>Categoría</th><th>Existencias</th><th>Estado</th></tr>{rows}</table></article></section>'
    else:
        options = ''.join(f'<option value="{p.get("id")}">{safe(p.get("name", ""))}</option>' for p in PRODUCTS)
        type_name = 'Entrada' if action == 'entry' else 'Salida'
        content = f'<section class="content"><div class="top"><div><h1 class="title">{title}</h1></div></div><div class="cols"><article class="card"><h3>Datos del movimiento</h3><form method="post" action="/actions/inventory"><input type="hidden" name="type" value="{type_name}"><label>Producto<select name="product_id" required>{options}</select></label><label> Sede<input value="Sede activa" readonly></label><label>Cantidad<input name="quantity" type="number" min="1" required></label><label>{"Motivo" if action == "exit" else "Nota"}<input name="note"></label><button class="btn">Guardar {"entrada" if action == "entry" else "salida"}</button></form></article><article class="card"><h3>Existencias recientes</h3><table><tr><th>Producto</th><th>Existencias</th><th>Estado</th></tr>{rows}</table></article></div></section>'
    html = shell(title, 'inventory', content, role)
    return append_notice(html, safe(notice)) if notice else html

def reports_screen(role, report=None, date_from='', date_to=''):
    report = report or []
    rows = ''.join(f'<tr><td>{safe(str(r.get("report_date", ""))[:10])}</td><td>#{safe(r.get("order_id", ""))}</td><td>Mesa {safe(r.get("table_number", ""))}</td><td>{safe(r.get("waiter", ""))}</td><td>{safe(r.get("location", ""))}</td><td>${int(float(r.get("total", 0) or 0)):,}</td><td>{safe(r.get("payment_method", "Sin pago"))}</td><td>{safe(r.get("products", ""))}</td></tr>' for r in report)
    export_query = urlencode({key: value for key, value in (('from', date_from), ('to', date_to)) if value})
    export_link = '/reports/export' + ('?' + export_query if export_query else '')
    content = f'<section class="content"><div class="top"><div><h1 class="title">Reportes</h1></div></div><article class="card"><form method="get" action="/reports" class="form-row"><label>Fecha inicial<input type="date" name="from" value="{safe(date_from)}"></label><label>Fecha final<input type="date" name="to" value="{safe(date_to)}"></label><button class="btn">Generar reporte</button></form></article><article class="card"><div class="top"><h3>Resultados</h3><a class="outline" href="{export_link}">Exportar a Excel</a></div><table><tr><th>Fecha</th><th>Pedido</th><th>Mesa</th><th>Mesero</th><th>Sede</th><th>Total</th><th>Medio de pago</th><th>Productos vendidos</th></tr>{rows}</table></article></section>'
    return shell('Reportes', 'reports', content, role)

def configuration_screen(role):
    cards = [
        ('Sedes', f'{len(LOCATIONS)} registradas', '/settings/locations'),
        ('Mesas', f'{len(TABLES)} mesas', '/tables'),
        ('Categorías', f'{len(CATEGORIES)} categorías', '/settings/categories'),
        ('Productos', f'{len(PRODUCTS)} productos', '/products'),
        ('Proveedores', f'{len(SUPPLIERS)} proveedores', '/suppliers'),
        ('Métodos de pago', f'{sum(bool(method.get("active")) for method in PAYMENT_METHODS)} activos', '/settings/payment-methods')
    ]
    cards_html = ''.join(f'<article class="card"><h3>{title}</h3><p>{value}</p><a class="outline" href="{link}">Administrar</a></article>' for title, value, link in cards)
    content = f'<section class="content"><div class="top"><div><h1 class="title">Parametrización del sistema</h1></div></div><div class="module-grid">{cards_html}</div></section>'
    return shell('Configuración', 'settings', content, role)

def section(name, role='Administrador', action='', order_id=''):
    title = next((label for label, key in NAV if key == name), 'Dashboard')
    cards = [('🛒', 'Pedidos activos', '18'), ('💳', 'Pendientes de pago', '7'), ('⏱', 'Tiempo promedio', '24 min')] if name == 'orders' else [('📦', 'Valor inventario', '$ 18,4M'), ('⚠', 'Alertas', '6'), ('↗', 'Movimientos hoy', '24')] if name == 'inventory' else [('▥', 'Ventas totales', '$ 12,8M'), ('▤', 'Pedidos cerrados', '142'), ('$', 'Ticket promedio', '$ 90.465')] if name == 'reports' else [('✓', 'Registros activos', '24'), ('+', 'Nuevos este mes', '8'), ('↗', 'Actualizados hoy', '12')]
    if name == 'tables':
        modules = ''.join(f'<article class="card module"><div class="icon">🪑</div><h3>{n}</h3><strong class="{s.lower()}">{s}</strong><p>{d}</p><a class="outline" href="/orders?role={role}&table={n}">{"Iniciar pedido" if s == "Libre" else "Ver pedido"}</a></article>' for n, s, d in TABLES)
    elif name == 'orders':
        modules = ''.join(f'<article class="card module"><div class="icon">🛒</div><h3>Pedido {num}</h3><p>{table} · {waiter}</p><strong class="title" style="font-size:24px">{total}</strong><br><a class="outline" href="/orders?role={role}&action=pay">{("Registrar pago" if role == "Cajero" else "Ver detalle")}</a></article>' for num, table, waiter, total in [('#1049','Mesa 04','Laura Gómez','$ 86.000'),('#1048','Mesa 02','Carlos Ruiz','$ 124.000'),('#1047','Mesa 06','Laura Gómez','$ 58.000')])
    else:
        modules = ''.join(f'<article class="card module"><div class="icon">{icon}</div><h3>{label}</h3><strong class="title" style="font-size:24px">{value}</strong><br><a class="outline" href="/{name}?role={role}&action=details">Ver detalles</a></article>' for icon, label, value in cards)
    operation = {'new': 'Formulario de registro abierto.', 'details': 'Detalle de la operación cargado.'}.get(action, '')
    if action == 'pay' and role == 'Cajero':
        operation = f'<div class="card"><h3>Registrar pago</h3><form method="post" action="/actions/payment"><input type="hidden" name="order_id" value="{order_id}"><label>Medio de pago</label><select name="method" required><option value="">Seleccionar</option><option>Efectivo</option><option>Credito</option><option>Debito</option></select><button class="btn">Confirmar pago</button></form></div>'
    notice = f'<div class="notice">{operation}</div>' if operation else ''
    content = f'<section class="content"><div class="top"><div><label class="kicker">Modulo operativo · {role}</label><h1 class="title">{title}</h1><p class="desc">Gestiona esta parte de BarWise desde un solo lugar.</p></div><a class="btn" href="/{name}?action=new">+ Nuevo registro</a></div>{notice}<div class="module-grid">{modules}</div></section>'
    return shell(title, name, content, role)

def users_screen(role, search='', edit_id=''):
    filtered = [user for user in USERS_FRONT if search.casefold() in
                (str(user.get('username', '')).casefold() + str(user.get('name', '')).casefold())]
    selected = next((user for user in USERS_FRONT if str(user.get('id')) == str(edit_id)), None)
    active_locations = [(LOCATION_IDS[i] if i < len(LOCATION_IDS) else i + 1, name)
                        for i, (name, _) in enumerate(LOCATIONS)
                        if LOCATION_ACTIVE.get(LOCATION_IDS[i] if i < len(LOCATION_IDS) else i + 1, True)]
    locations = ''.join(f'<option value="{location_id}">{safe(name)}</option>'
                        for location_id, name in active_locations)
    role_options = ''.join(
        f'<option value="{name}" {"selected" if selected and selected.get("role") == name else ""}>{name}</option>'
        for name in ('Cajero', 'Mesero', 'Administrador')
    )
    location_options = ''.join(
        f'<option value="{LOCATION_IDS[i] if i < len(LOCATION_IDS) else i + 1}" {"selected" if selected and selected.get("location_id") == (LOCATION_IDS[i] if i < len(LOCATION_IDS) else i + 1) else ""}>{safe(name)}</option>'
        for i, (name, _) in enumerate(LOCATIONS)
        if LOCATION_ACTIVE.get(LOCATION_IDS[i] if i < len(LOCATION_IDS) else i + 1, True)
    )
    rows = ''.join(
        f'<tr><td>{safe(u.get("username", ""))}</td><td>{safe(u.get("name", ""))}</td>'
        f'<td>{safe(next((name for i, (name, _) in enumerate(LOCATIONS) if (LOCATION_IDS[i] if i < len(LOCATION_IDS) else i + 1) == u.get("location_id")), "Todas" if u.get("role") == "Administrador" else "Sin sede"))}</td>'
        f'<td>{safe(u.get("role", ""))}</td><td><span class="{"status-ok" if u.get("active") else "status-off"}">{"Activo" if u.get("active") else "Inactivo"}</span></td>'
        f'<td><a class="outline" href="/users?edit={safe(u.get("id", ""))}">Editar</a> '
        f'<form method="post" action="/actions/user-status"><input type="hidden" name="user_id" value="{safe(u.get("id", ""))}">'
        f'<input type="hidden" name="active" value="{"0" if u.get("active") else "1"}"><button class="outline">{"Desactivar" if u.get("active") else "Activar"}</button></form></td></tr>'
        for u in filtered
    )
    form_title = 'Editar usuario' if selected else 'Registrar usuario'
    form_action = 'user-update' if selected else 'user'
    hidden_id = f'<input type="hidden" name="user_id" value="{safe(selected.get("id", ""))}">' if selected else ''
    username_field = (f'<label>Usuario<input value="{safe(selected.get("username", ""))}" readonly></label>' if selected
                      else '<label>Usuario<input name="username" required autocomplete="username"></label>')
    password_field = (f'<label>Nueva contraseña (opcional)<input name="password" type="password" minlength="8" autocomplete="new-password"></label>' if selected
                      else '<label>Contraseña<input name="password" type="password" minlength="8" required autocomplete="new-password"></label>')
    cancel = '<a class="outline" href="/users">Cancelar</a>' if selected else ''
    content = f'''<section class="content"><div class="top"><div><h1 class="title">Gestión de usuarios</h1><p class="desc">Solo el administrador puede asignar el perfil y la sede.</p></div></div><div class="cols"><article class="card"><h3>{form_title}</h3><form method="post" action="/actions/{form_action}">{hidden_id}<label>Nombre<input name="name" value="{safe(selected.get("name", "")) if selected else ""}" required></label><div class="form-row"><label>Sede<select name="location_id"><option value="">Seleccione sede</option>{location_options if selected else locations}</select></label><label>Perfil<select name="role">{role_options if selected else '<option value="Cajero">Cajero</option><option value="Mesero" selected>Mesero</option><option value="Administrador">Administrador</option>'}</select></label></div>{username_field}{password_field}<button class="btn">Guardar</button> {cancel}</form></article><article class="card"><form class="search-form" method="get" action="/users"><input name="search" value="{safe(search)}" placeholder="Buscar usuario…"><button class="outline">Buscar</button></form><table><tr><th>Usuario</th><th>Nombre</th><th>Sede</th><th>Perfil</th><th>Estado</th><th>Acción</th></tr>{rows or '<tr><td colspan="6">No hay usuarios para mostrar.</td></tr>'}</table></article></div></section><script>document.querySelectorAll('select[name="role"]').forEach(role => role.addEventListener('change', () => {{const location = role.closest('form').querySelector('select[name="location_id"]'); location.required = role.value !== 'Administrador'; location.disabled = role.value === 'Administrador'; if (location.disabled) location.value = '';}}));document.querySelectorAll('select[name="role"]').forEach(role => role.dispatchEvent(new Event('change')));</script>'''
    return shell('Usuarios', 'users', content, role)

class Handler(BaseHTTPRequestHandler):
    def session_user(self):
        cookie = self.headers.get('Cookie', '')
        session_id = next((part.split('=', 1)[1] for part in cookie.split(';') if part.strip().startswith('frontend_session=')), None)
        return SESSIONS.get(session_id)

    def do_GET(self):
        parsed = urlparse(unquote(self.path)); path = parsed.path.strip('/')
        query = parse_qs(parsed.query)
        if path.startswith('assets/'):
            asset_name = path.split('/', 1)[1]
            if '/' in asset_name or asset_name not in {'barwise-logo.svg', 'product-beer.svg', 'product-cocktail.svg', 'product-wine.svg', 'product-liquor.svg'}:
                self.send_response(404); self.end_headers(); return
            asset_path = os.path.join(os.path.dirname(__file__), 'assets', asset_name)
            try:
                with open(asset_path, 'rb') as asset:
                    body = asset.read()
                self.send_response(200); self.send_header('Content-Type', 'image/svg+xml'); self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
            except (FileNotFoundError, ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                self.send_response(404); self.end_headers()
            return
        user = self.session_user()
        if path == 'logout':
            if user:
                request('/api/auth/logout', method='POST', cookie=user['backend_cookie'])
            session_id = next((part.split('=', 1)[1] for part in self.headers.get('Cookie', '').split(';') if part.strip().startswith('frontend_session=')), None)
            if session_id: SESSIONS.pop(session_id, None)
            self.send_response(303); self.send_header('Location', '/'); self.send_header('Set-Cookie', 'frontend_session=; Max-Age=0; Path=/'); self.end_headers(); return
        if not user:
            self.send_html(login_page()); return
        global ACTIVE_LOCATION_ID, CURRENT_USER_NAME
        CURRENT_USER_NAME = user.get('name', user.get('username', 'Usuario'))
        try:
            active_location_id = int(query.get('location_id', [user.get('active_location_id', user.get('location_id') or 1)])[0])
        except ValueError:
            self.send_html(login_page('La sede seleccionada no es válida'), 400); return
        if user['role'] != 'Administrador':
            active_location_id = user.get('location_id')
        if not active_location_id:
            self.send_html(login_page('El usuario no tiene una sede asignada'), 403); return
        ACTIVE_LOCATION_ID = active_location_id
        user['active_location_id'] = active_location_id
        role = user['role']
        backend_cookie = user['backend_cookie']
        cache_key = f"{user.get('username', '')}:{active_location_id}"
        if path == 'reports/export' and role in ('Administrador', 'Cajero'):
            export_query = urlencode({key: query[key][0] for key in ('from', 'to') if query.get(key, [''])[0]})
            export_path = '/api/reports/sales.xlsx' + ('?' + export_query if export_query else '')
            status, content, content_type = download(export_path, cookie=backend_cookie, location_id=active_location_id)
            if status != 200:
                self.send_html(login_page(content.get('error', 'No fue posible exportar el reporte')), status); return
            self.send_file(content, 'barwise-reportes.xlsx', content_type); return
        cached = BOOTSTRAP_CACHE.get(cache_key)
        if cached and time.time() - cached[0] < 30:
            status, data = 200, cached[1]
        else:
            status, data, _ = request('/api/bootstrap', cookie=backend_cookie, location_id=active_location_id)
            if status == 200:
                BOOTSTRAP_CACHE[cache_key] = (time.time(), data)
        if status != 200:
            if status == 401:
                SESSIONS.pop(next((part.split('=', 1)[1] for part in self.headers.get('Cookie', '').split(';') if part.strip().startswith('frontend_session=')), ''), None)
                self.send_response(303); self.send_header('Location', '/'); self.send_header('Set-Cookie', 'frontend_session=; Max-Age=0; Path=/'); self.end_headers(); return
            self.send_html(login_page(data.get('error', 'No fue posible consultar el backend')), status if status >= 400 else 503); return
        global TABLES, LOCATIONS, LOCATION_IDS, LOCATION_ACTIVE, PRODUCTS, SUPPLIERS, CATEGORIES, PAYMENT_METHODS, TABLE_IDS, ORDERS_FRONT
        global TABLE_DETAILS, USERS_FRONT
        TABLES = [(table['name'], table['status'], f"{table['seats']} puestos") for table in data.get('tables', [])]
        TABLE_IDS = {table['name']: table['id'] for table in data.get('tables', [])}
        TABLE_DETAILS = data.get('tables', [])
        LOCATIONS = [(location['name'], location['address']) for location in data.get('locations', [])]
        LOCATION_IDS = [location['id'] for location in data.get('locations', [])]
        LOCATION_ACTIVE = {location['id']: location.get('active', True) for location in data.get('locations', [])}
        ACTIVE_LOCATION_ID = data.get('active_location_id', active_location_id)
        PRODUCTS = data.get('products', [])
        ORDERS_FRONT = data.get('orders', [])
        metadata_key = f'{cache_key}:{path}'
        cached_metadata = METADATA_CACHE.get(metadata_key)
        metadata = cached_metadata[1] if cached_metadata and time.time() - cached_metadata[0] < 30 else None
        if metadata is None:
            metadata = {'categories': [], 'payment_methods': [], 'users': [], 'suppliers': []}
            needs_categories = path in ('products', 'settings/categories', 'settings')
            needs_users = path in ('users', 'settings')
            needs_suppliers = path in ('products', 'suppliers', 'settings')
            if role == 'Administrador' and needs_categories:
                status_meta, value, _ = request('/api/categories', cookie=backend_cookie, location_id=ACTIVE_LOCATION_ID)
                metadata['categories'] = value.get('data', []) if status_meta == 200 else []
            needs_payment_methods = path in ('orders', 'reports', 'settings/payment-methods', 'settings')
            if role in ('Administrador', 'Cajero') and needs_payment_methods:
                status_meta, value, _ = request('/api/payment-methods', cookie=backend_cookie, location_id=ACTIVE_LOCATION_ID)
                metadata['payment_methods'] = value.get('data', []) if status_meta == 200 else []
            if role == 'Administrador' and needs_users:
                status_meta, value, _ = request('/api/users', cookie=backend_cookie, location_id=ACTIVE_LOCATION_ID)
                metadata['users'] = value.get('data', []) if status_meta == 200 else []
            if role == 'Administrador' and needs_suppliers:
                status_meta, value, _ = request('/api/suppliers', cookie=backend_cookie, location_id=ACTIVE_LOCATION_ID)
                metadata['suppliers'] = value.get('data', []) if status_meta == 200 else []
            METADATA_CACHE[metadata_key] = (time.time(), metadata)
        CATEGORIES = metadata['categories']
        PAYMENT_METHODS = metadata['payment_methods']
        USERS_FRONT = metadata['users']
        SUPPLIERS = metadata['suppliers']
        action = query.get('action', [''])[0]; order_id = query.get('order', [''])[0]
        order_notice = ''
        if path == 'orders' and action == 'details' or (
                path == 'orders' and action in ('invoice', 'close')
                and role in ('Cajero', 'Administrador')):
            order_status, order_data, _ = request(f'/api/orders/{order_id}', cookie=backend_cookie, location_id=ACTIVE_LOCATION_ID)
            if order_status == 200:
                ORDERS_FRONT = [item for item in ORDERS_FRONT if str(item.get('id')) != str(order_id)] + [order_data.get('data', {})]
            else:
                order_notice = safe(order_data.get('error', 'No se pudo consultar el pedido'))
        if path == 'reports' and role in ('Administrador', 'Cajero'):
            report_query = urlencode({key: query[key][0] for key in ('from', 'to') if query.get(key, [''])[0]})
            report_path = '/api/reports/sales' + ('?' + report_query if report_query else '')
            report_status, report_data, _ = request(report_path, cookie=backend_cookie, location_id=ACTIVE_LOCATION_ID)
            rows = report_data.get('data', []) if report_status == 200 else []
            html = reports_screen(role, rows, query.get('from', [''])[0], query.get('to', [''])[0])
            if report_status != 200:
                html = append_notice(html, safe(report_data.get("error", "No se pudo generar el reporte")))
            self.send_html(html); return
        if path == 'suppliers' and role == 'Administrador':
            html = suppliers_screen(role, query.get('search', [''])[0], query.get('edit', [''])[0])
        elif path == 'products': html = products_screen(role, query.get('search', [''])[0], query.get('edit', [''])[0])
        elif path == 'tables': html = tables_screen(role)
        elif path == 'settings' and role == 'Administrador': html = configuration_screen(role)
        elif path == 'settings/locations' and role == 'Administrador':
            html = locations_screen(role, query.get('edit', [''])[0])
        elif path == 'settings/categories' and role == 'Administrador': html = categories_screen(role)
        elif path == 'settings/payment-methods' and role == 'Administrador': html = payment_methods_screen(role)
        elif path == 'orders' and (
                not action or action in ('take', 'pending', 'add')):
            html = orders_screen(role, selected_table_id=query.get('table', [''])[0],
                                 selected_order_id=order_id if action == 'add' else '')
        elif path == 'orders' and action == 'details':
            html = cashier_orders_screen(role, action, order_id, order_notice)
        elif path == 'orders' and role in ('Cajero', 'Administrador') and action == 'pay': html = payment_screen(role, order_id)
        elif path == 'orders' and role in ('Cajero', 'Administrador'): html = cashier_orders_screen(role, action, order_id, order_notice)
        elif path == 'inventory': html = inventory_screen(role, action)
        elif path == 'users' and role == 'Administrador': html = users_screen(role, query.get('search', [''])[0], query.get('edit', [''])[0])
        elif path and path not in ROLE_ALLOWED[role]: html = section('dashboard', role)
        else: html = dashboard(role) if not path or path == 'dashboard' else section(path, role, action, order_id)
        self.send_html(html)

    def do_POST(self):
        global ORDERS_FRONT
        path = urlparse(self.path).path.strip('/').lower()
        if path == 'actions/order':
            user = self.session_user()
            if not user:
                self.send_html(login_page('Sign in to create orders.'), 401); return
            length = int(self.headers.get('Content-Length', 0)); values = parse_qs(self.rfile.read(length).decode('utf-8'))
            try:
                table_id = int(values.get('table_id', [''])[0])
                product_ids = values.get('product_id', [])
                quantity_values = values.get('quantity', [])
                items = [
                    {'product_id': int(product_id),
                     'quantity': int(quantity_values[index] if index < len(quantity_values)
                                     else values.get(f'quantity_{product_id}', ['1'])[0])}
                    for index, product_id in enumerate(product_ids)
                ]
            except ValueError:
                table_id = None
                items = []
            payload = {'table_id': table_id, 'items': items}
            status, data, _ = request('/api/orders', method='POST', cookie=user['backend_cookie'], body=payload,
                                      location_id=user.get('active_location_id', user.get('location_id')))
            invalidate_user_cache(user)
            if status < 300 and data.get('data'):
                new_order = data['data']
                ORDERS_FRONT.insert(0, new_order)
                for table in TABLE_DETAILS:
                    if str(table.get('id')) == str(table_id):
                        table['status'] = 'Ocupada'
                        table['order_id'] = new_order.get('id')
                        break
            message = 'Pedido registrado correctamente' if status < 300 else data.get('error', 'No fue posible registrar el pedido')
            self.send_html(orders_screen(user['role'], message)); return
        if path == 'actions/order-items':
            user = self.session_user()
            if not user:
                self.send_html(login_page('Sign in to add products to an order.'), 401); return
            length = int(self.headers.get('Content-Length', 0)); values = parse_qs(self.rfile.read(length).decode('utf-8'))
            try:
                order_id = int(values.get('order_id', [''])[0])
                product_ids = values.get('product_id', [])
                quantity_values = values.get('quantity', [])
                items = [{'product_id': int(product_id), 'quantity': int(values.get(f'quantity_{product_id}', ['1'])[0])}
                         for index, product_id in enumerate(product_ids)]
            except (IndexError, ValueError):
                order_id, items = None, []
            status, data, _ = request(f'/api/orders/{order_id}/items', method='POST',
                                      cookie=user['backend_cookie'], body={'items': items, 'replace': values.get('replace_items', ['0'])[0] == '1'},
                                      location_id=user.get('active_location_id', user.get('location_id')))
            invalidate_user_cache(user)
            if status < 300 and data.get('data'):
                updated = data['data']
                current = next((item for item in ORDERS_FRONT if str(item.get('id')) == str(order_id)), None)
                if current:
                    if values.get('replace_items', ['0'])[0] == '1':
                        current['items'] = updated.get('items_added', [])
                    else:
                        current.setdefault('items', []).extend(updated.get('items_added', []))
                    current['total'] = updated.get('total', current.get('total'))
            message = 'Productos agregados al pedido correctamente' if status < 300 else data.get('error', 'No fue posible agregar productos al pedido')
            self.send_html(orders_screen(user['role'], message)); return
        if path == 'actions/user':
            user = self.session_user()
            if not user or user['role'] != 'Administrador':
                self.send_html(login_page('Solo el Administrador puede registrar usuarios'), 403); return
            length = int(self.headers.get('Content-Length', 0)); values = parse_qs(self.rfile.read(length).decode('utf-8'))
            role = values.get('role', ['Mesero'])[0]
            raw_location_id = values.get('location_id', [''])[0]
            try:
                location_id = int(raw_location_id) if raw_location_id else None
            except ValueError:
                location_id = None
            payload = {'username': values.get('username', [''])[0], 'name': values.get('name', [''])[0], 'role': role, 'location_id': location_id, 'password': values.get('password', [''])[0]}
            status, data, _ = request('/api/users', method='POST', cookie=user['backend_cookie'], body=payload,
                                      location_id=user.get('active_location_id', user.get('location_id')))
            invalidate_user_cache(user)
            refresh_frontend_data(user)
            message = 'Usuario registrado correctamente' if status < 300 else data.get('error', 'No fue posible registrar el usuario')
            self.send_html(append_notice(users_screen(user['role']), safe(message))); return
        if path == 'actions/user-update':
            user = self.session_user()
            if not user or user['role'] != 'Administrador':
                self.send_html(login_page('Solo el Administrador puede modificar usuarios'), 403); return
            length = int(self.headers.get('Content-Length', 0)); values = parse_qs(self.rfile.read(length).decode('utf-8'))
            try:
                user_id = int(values.get('user_id', [''])[0])
                location_id = int(values.get('location_id', [''])[0]) if values.get('location_id', [''])[0] else None
            except ValueError:
                user_id, location_id = None, None
            payload = {'name': values.get('name', [''])[0], 'role': values.get('role', [''])[0],
                       'location_id': location_id, 'password': values.get('password', [''])[0]}
            status, data, _ = request(f'/api/users/{user_id}/update', method='POST', cookie=user['backend_cookie'],
                                      body=payload, location_id=user.get('active_location_id', user.get('location_id')))
            if status < 300:
                for session_id, session_user in tuple(SESSIONS.items()):
                    if str(session_user.get('id')) == str(user_id) and session_user is not user:
                        SESSIONS.pop(session_id, None)
            invalidate_user_cache(user)
            refresh_frontend_data(user)
            message = 'Usuario actualizado correctamente' if status < 300 else data.get('error', 'No fue posible actualizar el usuario')
            self.send_html(append_notice(users_screen(user['role']), safe(message))); return
        if path == 'actions/product':
            user = self.session_user()
            if not user or user['role'] != 'Administrador':
                self.send_html(login_page('Solo el Administrador puede registrar productos'), 403); return
            length = int(self.headers.get('Content-Length', 0)); values = parse_qs(self.rfile.read(length).decode('utf-8'))
            try:
                supplier_id = int(values.get('supplier_id', [''])[0]) if values.get('supplier_id', [''])[0] else None
            except ValueError:
                supplier_id = None
            payload = {'code': values.get('code', [''])[0], 'name': values.get('name', [''])[0], 'category': values.get('category', ['Licores'])[0],
                       'purchase_price': values.get('purchase_price', ['0'])[0], 'price': values.get('price', ['0'])[0],
                       'supplier_id': supplier_id, 'active': values.get('active', ['1'])[0] == '1'}
            status, data, _ = request('/api/products', method='POST', cookie=user['backend_cookie'], body=payload,
                                      location_id=user.get('active_location_id', user.get('location_id')))
            invalidate_user_cache(user)
            refresh_frontend_data(user)
            message = 'Producto registrado correctamente' if status < 300 else data.get('error', 'No fue posible registrar el producto')
            self.send_html(append_notice(products_screen(user['role']), safe(message))); return
        if path == 'actions/supplier':
            user = self.session_user()
            if not user or user['role'] != 'Administrador':
                self.send_html(login_page('Solo el Administrador puede registrar proveedores'), 403); return
            length = int(self.headers.get('Content-Length', 0)); values = parse_qs(self.rfile.read(length).decode('utf-8'))
            payload = {key: values.get(key, [''])[0] for key in ('name', 'identification', 'country', 'city', 'phone')}
            status, data, _ = request('/api/suppliers', method='POST', cookie=user['backend_cookie'], body=payload,
                                      location_id=user.get('active_location_id', user.get('location_id')))
            invalidate_user_cache(user)
            refresh_frontend_data(user)
            message = 'Proveedor registrado correctamente' if status < 300 else data.get('error', 'No fue posible registrar el proveedor')
            self.send_html(append_notice(suppliers_screen(user['role']), safe(message))); return
        if path in ('actions/location', 'actions/location-update', 'actions/table',
                    'actions/product-update', 'actions/supplier-update', 'actions/product-status',
                    'actions/supplier-status', 'actions/user-status',
                    'actions/category', 'actions/category-status', 'actions/payment-method-status'):
            user = self.session_user()
            if not user or user['role'] != 'Administrador':
                self.send_html(login_page('Solo el Administrador puede modificar la parametrización'), 403); return
            length = int(self.headers.get('Content-Length', 0)); values = parse_qs(self.rfile.read(length).decode('utf-8'))
            if path == 'actions/category':
                payload = {'name': values.get('name', [''])[0]}
                api_path = '/api/categories'
            elif path == 'actions/location-update':
                payload = {'name': values.get('name', [''])[0], 'address': values.get('address', [''])[0]}
                api_path = f'/api/locations/{values.get("location_id", [""])[0]}/update'
            elif path == 'actions/location':
                payload = {'name': values.get('name', [''])[0], 'address': values.get('address', [''])[0]}
                api_path = '/api/locations'
            elif path == 'actions/supplier-update':
                payload = {key: values.get(key, [''])[0] for key in ('name', 'identification', 'country', 'city', 'phone')}
                api_path = f'/api/suppliers/{values.get("supplier_id", [""])[0]}/update'
            elif path == 'actions/table':
                try:
                    payload = {'location_id': int(values.get('location_id', [''])[0]),
                               'table_number': int(values.get('table_number', [''])[0]),
                               'seats': int(values.get('seats', ['4'])[0])}
                except ValueError:
                    payload = {}
                api_path = '/api/tables'
            elif path == 'actions/product-update':
                try:
                    supplier_id = int(values.get('supplier_id', [''])[0]) if values.get('supplier_id', [''])[0] else None
                except ValueError:
                    supplier_id = None
                payload = {'code': values.get('code', [''])[0], 'name': values.get('name', [''])[0],
                           'category': values.get('category', [''])[0], 'supplier_id': supplier_id,
                           'purchase_price': values.get('purchase_price', [''])[0], 'price': values.get('price', [''])[0],
                           'active': values.get('active', ['1'])[0] == '1'}
                api_path = f'/api/products/{values.get("product_id", [""])[0]}/update'
            else:
                entity, field = {
                    'actions/product-status': ('products', 'product_id'),
                    'actions/supplier-status': ('suppliers', 'supplier_id'),
                    'actions/user-status': ('users', 'user_id'),
                    'actions/category-status': ('categories', 'category_id'),
                    'actions/payment-method-status': ('payment-methods', 'payment_method_id'),
                }[path]
                record_id = values.get(field, [''])[0]
                payload = {'active': values.get('active', ['0'])[0] == '1'}
                api_path = f'/api/{entity}/{record_id}/status'
            status, data, _ = request(api_path, method='POST', cookie=user['backend_cookie'],
                                      body=payload, location_id=user.get('active_location_id', user.get('location_id')))
            invalidate_user_cache(user)
            if path == 'actions/table' and payload.get('location_id'):
                # El administrador puede registrar en cualquier sede; mostrar inmediatamente esa sede.
                user['active_location_id'] = payload['location_id']
                refresh_frontend_data(user, payload['location_id'])
            else:
                refresh_frontend_data(user)
            message = data.get('error', 'Cambios guardados correctamente') if status < 300 else data.get('error', 'No fue posible guardar los cambios')
            if path in ('actions/location', 'actions/location-update'):
                page = locations_screen(user['role'])
            elif path == 'actions/table':
                page = tables_screen(user['role'])
            elif path.startswith('actions/product'):
                page = products_screen(user['role'])
            elif path.startswith('actions/supplier'):
                page = suppliers_screen(user['role'])
            elif path.startswith('actions/category'):
                page = categories_screen(user['role'])
            elif path.startswith('actions/payment-method'):
                page = payment_methods_screen(user['role'])
            else:
                page = users_screen(user['role'])
            self.send_html(append_notice(page, safe(message))); return
        if path == 'actions/inventory':
            user = self.session_user()
            if not user or user['role'] != 'Administrador':
                self.send_html(login_page('Solo el Administrador puede modificar el inventario'), 403); return
            length = int(self.headers.get('Content-Length', 0)); values = parse_qs(self.rfile.read(length).decode('utf-8'))
            movement = values.get('type', [''])[0]
            payload = {'product_id': int(values.get('product_id', ['0'])[0]), 'quantity': int(values.get('quantity', ['0'])[0]), 'type': movement, 'note': values.get('note', [''])[0]}
            status, data, _ = request('/api/inventory/movements', method='POST', cookie=user['backend_cookie'], body=payload,
                                      location_id=user.get('active_location_id', user.get('location_id')))
            invalidate_user_cache(user)
            refresh_frontend_data(user)
            message = 'Movimiento registrado correctamente' if status < 300 else data.get('error', 'No fue posible registrar el movimiento')
            self.send_html(inventory_screen(user['role'], 'entry' if movement == 'Entrada' else 'exit', safe(message))); return
        if path == 'actions/payment':
            user = self.session_user()
            if not user or user['role'] not in ('Cajero', 'Administrador'):
                self.send_html(login_page('No tienes permiso para registrar pagos'), 403); return
            length = int(self.headers.get('Content-Length', 0)); values = parse_qs(self.rfile.read(length).decode('utf-8'))
            try:
                order_id = int(values.get('order_id', [''])[0])
            except ValueError:
                order_id = None
            status, data, _ = request('/api/payments', method='POST', cookie=user['backend_cookie'],
                                      body={'order_id': order_id, 'method': values.get('method', [''])[0]},
                                      location_id=user.get('active_location_id', user.get('location_id')))
            invalidate_user_cache(user)
            if status < 300:
                order_status, order_data, _ = request(
                    f'/api/orders/{order_id}', cookie=user['backend_cookie'],
                    location_id=user.get('active_location_id', user.get('location_id')))
                if order_status == 200:
                    paid_order = order_data.get('data', {})
                else:
                    paid_order = next(
                        (item.copy() for item in ORDERS_FRONT if str(item.get('id')) == str(order_id)),
                        data.get('data', {}).copy())
                    paid_order.update(data.get('data', {}))
                    paid_order['invoice_number'] = data.get('invoice', {}).get('number')
                if paid_order.get('invoice_number') and paid_order.get('items'):
                    ORDERS_FRONT = [item for item in ORDERS_FRONT
                                    if str(item.get('id')) != str(order_id)] + [paid_order]
                    self.send_html(cashier_orders_screen(user['role'], 'invoice', str(order_id))); return
                message = 'El pago se registró, pero no fue posible cargar la factura. Intenta abrir el pedido nuevamente.'
                self.send_html(append_notice(cashier_orders_screen(user['role']), safe(message)), 502); return
            refresh_frontend_data(user)
            message = data.get('error', 'No fue posible registrar el pago')
            self.send_html(cashier_orders_screen(user['role'], 'details', str(order_id or ''), safe(message))); return
        if path == 'actions/close':
            user = self.session_user()
            if not user or user['role'] not in ('Cajero', 'Administrador'):
                self.send_html(login_page('No tienes permiso para cerrar pedidos'), 403); return
            length = int(self.headers.get('Content-Length', 0)); values = parse_qs(self.rfile.read(length).decode('utf-8'))
            try:
                order_id = int(values.get('order_id', [''])[0])
            except ValueError:
                order_id = None
            status, data, _ = request('/api/orders/close', method='POST', cookie=user['backend_cookie'],
                                      body={'order_id': order_id},
                                      location_id=user.get('active_location_id', user.get('location_id')))
            invalidate_user_cache(user)
            refresh_frontend_data(user)
            message = 'Pedido cerrado correctamente' if status < 300 else data.get('error', 'No fue posible cerrar el pedido')
            if status < 300:
                order_status, order_data, _ = request(f'/api/orders/{order_id}', cookie=user['backend_cookie'],
                                                      location_id=user.get('active_location_id', user.get('location_id')))
                if order_status == 200:
                    ORDERS_FRONT.append(order_data.get('data', {}))
            self.send_html(cashier_orders_screen(user['role'], 'invoice' if status < 300 else 'close',
                                                 str(order_id or ''), safe(message))); return
        if path not in ('', 'login'):
            self.send_html(login_page('Ruta no encontrada'), 404); return
        length = int(self.headers.get('Content-Length', 0))
        values = parse_qs(self.rfile.read(length).decode('utf-8'))
        username = values.get('username', [''])[0]; password = values.get('password', [''])[0]
        status, data, backend_cookie = request('/api/auth/login', method='POST', body={'username': username, 'password': password})
        if status != 200:
            self.send_html(login_page(data.get('error', 'Usuario o contraseña incorrectos')), 401); return
        session_id = secrets.token_urlsafe(24)
        SESSIONS[session_id] = {'username': data['user']['username'], 'name': data['user'].get('name', data['user']['username']), 'role': data['user']['role'], 'location_id': data['user'].get('location_id'), 'backend_cookie': backend_cookie.split(';', 1)[0]}
        self.send_response(303); self.send_header('Location', '/'); self.send_header('Set-Cookie', f'frontend_session={session_id}; HttpOnly; SameSite=Lax; Path=/'); self.end_headers()

    def send_html(self, html, status=200):
        body = html.encode('utf-8')
        try:
            self.send_response(status); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass
    def send_file(self, content, filename, content_type):
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        try:
            self.wfile.write(content)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass
    def log_message(self, *_):
        pass

if __name__ == '__main__':
    print('BarWise frontend: http://127.0.0.1:5000')
    HTTPServer(('127.0.0.1', 5000), Handler).serve_forever()
