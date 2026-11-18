NAV = [('Dashboard', 'dashboard'), ('Orders', 'orders'), ('Tables', 'tables'), ('Products', 'products'), ('Inventory', 'inventory'), ('Suppliers', 'suppliers'), ('Users', 'users'), ('Reports', 'reports'), ('Settings', 'settings')]
ROLE_ALLOWED = {
    'Administrador': {'dashboard', 'orders', 'tables', 'products', 'inventory', 'suppliers', 'users', 'reports', 'settings'},
    'Cajero': {'dashboard', 'orders', 'tables', 'products', 'reports'},
    'Mesero': {'dashboard', 'orders', 'tables', 'products'},
}
