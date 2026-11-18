"""Algoritmos de negocio usados por BarWise.

Se mantienen sin dependencias externas para que puedan probarse y explicarse
en la entrega de Algoritmos.
"""


def binary_search_products(products, query):
    """Busca un producto por nombre o código en O(log n)."""
    ordered = sorted(products, key=lambda p: (str(p.get('name', '')).lower(), str(p.get('code', '')).lower()))
    target = str(query or '').strip().lower()
    left, right = 0, len(ordered) - 1
    while left <= right:
        middle = (left + right) // 2
        current = str(ordered[middle].get('name', '')).lower()
        code = str(ordered[middle].get('code', '')).lower()
        if target == current or target == code:
            return ordered[middle]
        if current < target:
            left = middle + 1
        else:
            right = middle - 1
    return None


def merge_sort_products(products, key='name', reverse=False):
    """Ordena productos mediante Merge Sort en O(n log n)."""
    values = list(products)

    def merge(left, right):
        result = []
        while left and right:
            left_value = left[0].get(key, 0)
            right_value = right[0].get(key, 0)
            if (left_value <= right_value) != reverse:
                result.append(left.pop(0))
            else:
                result.append(right.pop(0))
        return result + left + right

    if len(values) <= 1:
        return values
    middle = len(values) // 2
    return merge(merge_sort_products(values[:middle], key, reverse),
                 merge_sort_products(values[middle:], key, reverse))


def inventory_alerts(inventory):
    """Detecta existencias iguales o menores al mínimo configurado."""
    return [item for item in inventory
            if float(item.get('quantity', item.get('stock', 0)) or 0) <=
            float(item.get('minimum_quantity', item.get('minimum', 0)) or 0)]


def calculate_order_total(items):
    """Calcula el total de una orden y sus subtotales."""
    details, total = [], 0
    for item in items:
        quantity = float(item.get('quantity', 0) or 0)
        price = float(item.get('price', item.get('unit_price', 0)) or 0)
        subtotal = quantity * price
        details.append({**item, 'subtotal': subtotal})
        total += subtotal
    return {'items': details, 'total': total}


def sales_summary(rows):
    """Agrupa ventas por fecha y calcula pedidos, ventas y promedio."""
    summary = {}
    for row in rows:
        date = str(row.get('report_date') or row.get('date') or 'Sin fecha')
        bucket = summary.setdefault(date, {'date': date, 'orders': 0, 'sales': 0})
        bucket['orders'] += 1
        bucket['sales'] += float(row.get('total', row.get('total_sales', 0)) or 0)
    for bucket in summary.values():
        bucket['average_order'] = bucket['sales'] / bucket['orders'] if bucket['orders'] else 0
    return sorted(summary.values(), key=lambda item: item['date'], reverse=True)


def linear_search_products(products, query):
    """Busca coincidencias parciales en nombre, código o categoría en O(n)."""
    target = str(query or '').strip().lower()
    if not target:
        return list(products)
    return [product for product in products
            if target in ' '.join(str(product.get(field, ''))
                                  for field in ('name', 'code', 'category')).lower()]


def quick_sort_orders(orders, key='total', reverse=True):
    """Ordena pedidos con Quick Sort promedio O(n log n)."""
    values = list(orders)
    if len(values) <= 1:
        return values
    pivot = values[len(values) // 2].get(key, 0) or 0
    before = [item for item in values if ((item.get(key, 0) or 0) > pivot) == reverse]
    equal = [item for item in values if (item.get(key, 0) or 0) == pivot]
    after = [item for item in values if ((item.get(key, 0) or 0) < pivot) == reverse]
    return quick_sort_orders(before, key, reverse) + equal + quick_sort_orders(after, key, reverse)


def consolidate_order_items(items):
    """Consolida productos repetidos usando una tabla hash en O(n)."""
    consolidated = {}
    for item in items:
        product_id = item.get('product_id')
        if product_id is None:
            continue
        if product_id not in consolidated:
            consolidated[product_id] = {**item, 'quantity': 0}
        consolidated[product_id]['quantity'] += int(item.get('quantity', 0) or 0)
    return list(consolidated.values())


def paginate(items, page=1, page_size=10):
    """Devuelve una página de resultados y sus metadatos en O(1) para el corte."""
    page = max(1, int(page))
    page_size = max(1, min(100, int(page_size)))
    start = (page - 1) * page_size
    return {'items': list(items)[start:start + page_size], 'page': page,
            'page_size': page_size, 'total': len(items),
            'pages': (len(items) + page_size - 1) // page_size}


def calculate_change(amount, received, denominations=None):
    """Calcula el cambio con estrategia voraz usando las denominaciones mayores."""
    amount, received = int(amount), int(received)
    if received < amount:
        raise ValueError('El valor recibido es insuficiente')
    denominations = sorted(denominations or [50000, 20000, 10000, 5000, 2000, 1000, 500], reverse=True)
    remaining, change = received - amount, []
    for denomination in denominations:
        count, remaining = divmod(remaining, denomination)
        change.extend([denomination] * count)
    return {'total': received - amount, 'denominations': change}


def inventory_projection(current, daily_consumption, days=7):
    """Proyecta existencias futuras y marca si el producto quedará agotado."""
    current, daily_consumption, days = float(current), float(daily_consumption), int(days)
    projected = max(0, current - daily_consumption * days)
    return {'current': current, 'days': days, 'projected': projected,
            'will_be_empty': projected <= 0}


def top_selling_products(items, limit=5):
    """Construye un ranking de productos vendidos usando acumulación y ordenamiento."""
    totals = {}
    for item in items:
        key = item.get('product_id', item.get('name'))
        bucket = totals.setdefault(key, {'product_id': key, 'name': item.get('name', 'Product'), 'quantity': 0, 'sales': 0})
        bucket['quantity'] += float(item.get('quantity', 0) or 0)
        bucket['sales'] += float(item.get('quantity', 0) or 0) * float(item.get('price', item.get('unit_price', 0)) or 0)
    return quick_sort_orders(list(totals.values()), 'quantity')[:max(0, int(limit))]
