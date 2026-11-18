# Arquitectura de BarWise

## Comunicación

```text
Navegador
   |
   v
frontend/app.py :5000
   |
   | api_client.py (HTTP + cookie de sesión)
   v
backend/app.py :5001
   |
   +-- auth_service.py
   +-- security.py
   +-- mysql_repository.py (consultas y persistencia MySQL)
   +-- mysql_database.py (conexión MySQL y variables de entorno)
   +-- barwise_schema.sql (modelo y migración inicial MySQL)
```

El frontend no autentica ni almacena usuarios. Cuando se envía el formulario de login, `frontend/api_client.py` hace `POST /api/auth/login` al backend. El backend responde con una cookie de sesión. El frontend conserva esa cookie en su sesión y la reenvía en cada consulta.

Después del login, el frontend consulta `GET /api/bootstrap`; esa respuesta carga la información de la sede permitida, mesas, productos y pedidos. Los permisos son decididos en el backend y el frontend solo oculta los módulos que el usuario no puede utilizar.

## Ejecución

Abrir dos terminales:

```powershell
cd BarWise/backend
python app.py
```

```powershell
cd BarWise/frontend
python app.py
```

El backend debe estar activo antes de abrir el frontend.
## Sprint 2 — HU-015 a HU-024

El incremento de Sprint 2 está cubierto con persistencia MySQL:

- HU-015: activar/desactivar productos mediante endpoints administrativos.
- HU-016 a HU-018: registrar, consultar y modificar proveedores.
- HU-019 a HU-022: inventario independiente por sede, entradas, salidas y disponibilidad.
- HU-023: registrar pedidos con sede, mesa, mesero, productos, cantidades y total; la mesa pasa a Ocupada.
- HU-024: consultar pedidos abiertos para Cajero y Administrador.

Las salidas validan existencia suficiente, los productos inactivos no se pueden agregar a pedidos y los pedidos se cargan nuevamente desde MySQL al reiniciar el backend.
## Sprint 1 — HU-001 a HU-014

El incremento de Sprint 1 también está implementado y persistido en MySQL:

- HU-001 a HU-003: inicio de sesión, validación de credenciales y permisos por perfil.
- HU-004 a HU-007: registrar, consultar, modificar y activar/desactivar usuarios.
- HU-008 a HU-009: registrar y consultar sedes; el Administrador puede cambiar de sede.
- HU-010 a HU-011: administrar mesas por sede y consultar sus estados.
- HU-012 a HU-014: registrar, consultar, modificar y activar/desactivar productos y categorías.

El backend aplica la autorización aunque el frontend oculte módulos, y los datos de sedes, usuarios, mesas, categorías y productos se consultan desde MySQL.
