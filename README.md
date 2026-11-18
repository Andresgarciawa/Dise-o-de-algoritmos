# BarWise

Aplicación web para la operación de bares, con frontend HTTP en Python y API conectada a MySQL:

- `frontend/`: interfaz web servida con la biblioteca estándar de Python.
- `backend/`: API HTTP y persistencia MySQL.

## Instalar dependencias del backend

```bash
cd backend
python -m pip install -r requirements.txt
```

Configura las variables de conexión MySQL descritas más abajo antes de iniciar los servicios.

## Ejecutar los servicios

```bash
cd backend
python app.py
```

En otra terminal:

```bash
cd frontend
python app.py
```

Abre `http://127.0.0.1:5000`. La API escucha en `http://127.0.0.1:5001`.

## Pruebas

Desde la carpeta `BarWise`, ejecuta las pruebas de interfaz con:

```bash
python -m unittest discover -s frontend -p "test_*.py"
```

## Backend y autenticacion

El backend ya incluye login y control de permisos por perfil. Usuarios de prueba:

- `admin` / `BarWise2026!` — Administrador
- `cajero` / `BarWise2026!` — Cajero
- `mesero` / `BarWise2026!` — Mesero

Login:

```text
POST /api/auth/login
{"username":"admin","password":"BarWise2026!"}
```

La respuesta entrega un token. Para consultar rutas protegidas se envia:

```text
Authorization: Bearer <token>
```

Rutas iniciales: `/api/me`, `/api/locations`, `/api/locations/1/tables`, `/api/tables`, `/api/products`, `/api/inventory`, `/api/orders`, `/api/payments`, `/api/users` y `/api/reports/sales`.

## Base de datos MySQL

El script de inicialización está en `backend/barwise_schema.sql`. **Recrea el esquema y elimina las tablas existentes**; respalda la base de datos antes de ejecutarlo en un entorno con datos.

```bash
mysql -u root -p < backend/barwise_schema.sql
```

Incluye usuarios, roles, sedes, mesas, productos, categorías, proveedores, inventario, movimientos, pedidos, pagos, facturas, sesiones y una vista de ventas por sede.

La API usa MySQL para autenticar usuarios y persistir sesiones, pedidos, pagos, facturas, inventario, catálogos y auditoría. La exportación de reportes XLSX utiliza `openpyxl`, declarado en `backend/requirements.txt`.

### Algoritmos implementados

El backend incluye cinco algoritmos en `backend/algorithms.py`, integrados mediante `GET /api/algorithms` para el perfil Administrador:

1. Búsqueda binaria de productos por nombre o código (`O(log n)`).
2. Merge Sort para ordenar productos por existencias (`O(n log n)`).
3. Detección lineal de alertas de inventario (`O(n)`).
4. Cálculo de subtotales y total de pedidos (`O(n)`).
5. Agrupación de ventas por fecha y promedio por pedido (`O(n)`).
6. Búsqueda lineal parcial del catálogo (`O(n)`).
7. Quick Sort para ranking de pedidos (`O(n log n)` promedio).
8. Consolidación de productos repetidos mediante tabla hash (`O(n)`).
9. Paginación de resultados del catálogo.
10. Cambio de dinero con estrategia voraz.
11. Proyección de existencias por consumo diario.
12. Ranking de productos más vendidos.

Sus pruebas automatizadas están en `backend/test_algorithms.py`.

Operaciones de negocio incluidas: todos los usuarios autenticados pueden ver las mesas de su sede en tarjetas, abrir pedidos desde mesas libres y agregar productos a cualquier pedido abierto de su sede mediante `POST /api/orders/{id}/items`; el sistema valida existencias y descuenta el inventario. Al confirmar un pago, la API registra el medio de pago, cierra el pedido, libera la mesa y genera la factura interna en una sola transacción. El frontend muestra la factura imprimible con su número persistido, la sede, los productos, el total y el medio de pago. No se genera facturación electrónica.

Cada mesa pertenece a una sede y su número es único dentro de esa sede. Sus únicos estados son `Libre` y `Ocupada`: crear un pedido la ocupa y confirmar el pago la libera. No se admiten reservas ni combinación de mesas; las mesas no se desactivan desde la gestión.

Para actualizar una base existente desde los estados anteriores, respalda la base y ejecuta `mysql -u root -p < backend/migrations/20261104_table_states.sql`. La migración marca como ocupadas las mesas que tengan pedidos abiertos o pagados pendientes de cierre y deja las demás libres. En instalaciones nuevas, el esquema ya define únicamente los dos estados permitidos.

Las sedes iniciales son Calle 85 y Galerias. Cada mesa pertenece a una sede mediante `location_id`; el mismo criterio se usa para inventario, pedidos y reportes. El catálogo está limitado a bebidas alcohólicas: cervezas, cocteles, licores y vinos; no se contemplan comidas.

El administrador (`admin`) tiene acceso a todas las sedes. Para cambiar su sede activa debe enviar el encabezado `X-Location-ID: 1` o `X-Location-ID: 2`. El cajero y el mesero tienen una sede fija: el cajero demo opera en Calle 85 y el mesero demo en Galerias. Si intentan acceder a otra sede, la API responde `403`.

## Conexion local con MySQL Workbench

Las credenciales no se guardan en los archivos del proyecto. Configura la sesión actual de PowerShell así:

```powershell
$env:BARWISE_DB_HOST="127.0.0.1"
$env:BARWISE_DB_PORT="3306"
$env:BARWISE_DB_USER="root"
$env:BARWISE_DB_PASSWORD="TU_PASSWORD_LOCAL"
$env:BARWISE_DB_NAME="barwise"
```

Instala el conector y ejecuta el script SQL en MySQL Workbench:

```powershell
cd BarWise/backend
python -m pip install -r requirements.txt
```

La conexión está centralizada en `backend/mysql_database.py` y valida MySQL con `SELECT 1`.

## Parámetros y perfiles

Los perfiles son los tres roles predefinidos (Administrador, Cajero y Mesero); solo el administrador puede asignar o modificar el perfil y la sede de otros usuarios, pero no puede crear permisos personalizados. Al cambiar la configuración de un usuario, sus otras sesiones se invalidan. País y ciudad se capturan como texto al registrar proveedores; la sede conserva su dirección como texto. No hay catálogos independientes de países/ciudades ni un campo de ciudad normalizado para las sedes.




admin / BarWise2026!
cajero / BarWise2026!
mesero / BarWise2026!
