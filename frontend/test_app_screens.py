import unittest
from io import BytesIO
from unittest.mock import patch

import app
from config import ROLE_ALLOWED


class FrontendScreenTests(unittest.TestCase):
    def setUp(self):
        app.PRODUCTS = [{'id': 1, 'name': '<img src=x onerror=alert(1)>', 'price': 12000, 'stock': 4, 'active': True}]
        app.TABLE_DETAILS = [
            {'id': 8, 'name': 'Mesa 08', 'status': 'Libre', 'seats': 4, 'location_id': 8},
            {'id': 9, 'name': 'Mesa 09', 'status': 'Ocupada', 'seats': 2, 'location_id': 8, 'order_id': 17},
        ]
        app.LOCATIONS = [('Sede Norte', 'Calle 12'), ('Sede Sur', 'Carrera 4')]
        app.LOCATION_IDS = [3, 8]
        app.LOCATION_ACTIVE = {}
        app.SUPPLIERS = [{
            'id': 5,
            'name': 'Proveedor A',
            'identification': 'ABC-5',
            'country': 'Colombia',
            'city': 'Bogota',
            'phone': '3000',
            'active': True,
        }]
        app.CATEGORIES = [
            {'id': 1, 'name': 'Cervezas', 'active': True},
            {'id': 2, 'name': 'Inactiva', 'active': False},
        ]
        app.PAYMENT_METHODS = [
            {'id': 1, 'name': 'Efectivo', 'active': True},
            {'id': 2, 'name': 'Credito', 'active': False},
            {'id': 3, 'name': 'Debito', 'active': True},
        ]
        app.ORDERS_FRONT = [{
            'id': 17,
            'table_id': 9,
            'table_name': 'Mesa 09',
            'waiter': 'Laura Gómez',
            'status': 'Abierto',
            'location_id': 3,
            'total': 24000,
            'items': [{'name': 'Cerveza', 'quantity': 2, 'price': 12000}],
        }]
        app.USERS_FRONT = [{
            'id': 4,
            'username': 'mesero',
            'name': 'Laura Gómez',
            'role': 'Mesero',
            'location_id': 3,
            'active': True,
        }]
        app.CURRENT_USER_NAME = 'Laura Gómez'

    def test_order_form_posts_selected_table_and_escapes_product_names(self):
        html = app.order_screen('Mesero', '8')

        self.assertIn('name="table_id"', html)
        self.assertIn('value="8" selected', html)
        self.assertIn('&lt;img src=x onerror=alert(1)&gt;', html)
        self.assertNotIn('<img src=x onerror=alert(1)>', html)
        self.assertNotIn('innerHTML', html)

    def test_products_use_active_categories_only(self):
        html = app.products_screen('Administrador')

        self.assertIn('Cervezas', html)
        self.assertNotIn('value="Inactiva"', html)

    def test_payment_screen_uses_active_payment_methods_only(self):
        html = app.payment_screen('Cajero', '17')

        self.assertIn('value="Efectivo"', html)
        self.assertIn('value="Debito"', html)
        self.assertIn('<b>Cash</b>', html)
        self.assertIn('<b>Debit card</b>', html)
        self.assertNotIn('value="Credito"', html)
        self.assertIn('data-total="24000"', html)
        self.assertIn('payment-option-total', html)

    def test_payment_screen_accepts_mysql_decimal_order_total(self):
        app.ORDERS_FRONT[0]['total'] = '108000.00'

        html = app.payment_screen('Cajero', '17')

        self.assertIn('$108,000', html)
        self.assertIn('data-total="108000"', html)

    def test_cashier_order_flow_selects_order_then_displays_payment_or_close_action(self):
        listing = app.cashier_orders_screen('Cajero')
        details = app.cashier_orders_screen('Cajero', 'details', '17')

        self.assertIn('Select order', listing)
        self.assertIn('orders?action=details&order=17', listing)
        self.assertIn('Record payment', details)
        self.assertIn('Laura Gómez', details)
        app.ORDERS_FRONT[0]['status'] = 'Pagado'
        paid_details = app.cashier_orders_screen('Cajero', 'details', '17')
        self.assertIn('Continue to checkout', paid_details)
        app.ORDERS_FRONT[0].update({'status': 'Cerrado', 'invoice_number': 'FV-0000017'})
        closed_details = app.cashier_orders_screen('Cajero', 'details', '17')
        self.assertIn('View invoice', closed_details)
        self.assertIn('orders?action=invoice&order=17', closed_details)

    def test_successful_payment_displays_invoice_without_separate_close_action(self):
        user = {'role': 'Cajero', 'backend_cookie': 'session', 'active_location_id': 3}
        order = {
            'id': 17,
            'table_id': 9,
            'table_name': 'Mesa 09',
            'location_id': 3,
            'status': 'Cerrado',
            'total': 24000,
            'invoice_number': 'FV-0000017',
            'payment': {'method': 'Efectivo'},
            'items': [{'name': 'Cerveza', 'quantity': 2, 'price': 12000}],
        }
        handler = app.Handler.__new__(app.Handler)
        handler.path = '/actions/payment'
        body = b'order_id=17&method=Efectivo'
        handler.headers = {'Content-Length': str(len(body))}
        handler.rfile = BytesIO(body)
        handler.session_user = lambda: user
        rendered = []
        handler.send_html = lambda html, status=200: rendered.append((html, status))

        with patch.object(app, 'invalidate_user_cache'), patch.object(
            app, 'request', side_effect=[
                (200, {'data': order, 'invoice': {'number': 'FV-0000017'}}, ''),
                (200, {'data': order}, ''),
            ]) as request:
            handler.do_POST()

        self.assertEqual(len(rendered), 1)
        self.assertEqual(rendered[0][1], 200)
        self.assertIn('FV-0000017', rendered[0][0])
        self.assertIn('Cash', rendered[0][0])
        self.assertNotIn('/actions/close', rendered[0][0])
        self.assertEqual(request.call_count, 2)

    def test_edit_button_opens_read_only_order_summary_for_all_profiles(self):
        for role in ('Mesero', 'Cajero', 'Administrador'):
            with self.subTest(role=role):
                summary = app.cashier_orders_screen(role, 'details', '17')
                self.assertIn('Order details', summary)
                self.assertIn('Cerveza', summary)
                if role == 'Mesero':
                    self.assertNotIn('Record payment</a>', summary)
                else:
                    self.assertIn('Record payment', summary)

    def test_order_views_render_mysql_decimal_quantities(self):
        app.ORDERS_FRONT[0]['items'] = [{
            'name': 'Cerveza',
            'quantity': '3.00',
            'price': '12000.00',
        }]

        for action in ('details', 'close'):
            with self.subTest(action=action):
                html = app.cashier_orders_screen('Cajero', action, '17')
                self.assertIn('<td>3</td>', html)
                self.assertIn('$36,000', html)

        app.ORDERS_FRONT[0]['invoice_number'] = 'FV-0000017'
        invoice = app.cashier_orders_screen('Cajero', 'invoice', '17')
        self.assertIn('<td>3</td>', invoice)
        self.assertIn('$36,000', invoice)

        payment = app.payment_screen('Cajero', '17')
        self.assertIn('<td>3</td>', payment)
        self.assertIn('$36,000', payment)

    def test_orders_screen_shows_interactive_table_cards_without_the_order_table(self):
        waiter_html = app.orders_screen('Mesero')
        cashier_html = app.orders_screen('Cajero')
        admin_html = app.orders_screen('Administrador')

        self.assertIn('class="order-tables-grid"', waiter_html)
        self.assertIn('data-open-modal="new-order-modal-8"', waiter_html)
        self.assertIn('data-open-modal="add-products-modal-17"', waiter_html)
        self.assertIn('data-open-modal="edit-order-modal-17">Edit</button>', waiter_html)
        self.assertIn('id="edit-order-modal-17"', waiter_html)
        self.assertIn('data-open-modal="add-products-modal-17">Add</button>', waiter_html)
        self.assertIn('disabled title="Only cashiers and administrators can record payments">Pay</button>', waiter_html)
        self.assertIn('Occupied', waiter_html)
        self.assertIn('Available', waiter_html)
        self.assertNotIn('Reserved', waiter_html)
        self.assertNotIn('<table', waiter_html)
        self.assertNotIn('order-search', waiter_html)
        self.assertIn('id="new-order-modal-8"', waiter_html)
        self.assertIn('name="table_id" value="8"', waiter_html)
        self.assertIn('id="add-products-modal-17"', waiter_html)
        self.assertIn('data-open-modal="new-order-modal-8"', cashier_html)
        self.assertIn('data-open-modal="add-products-modal-17"', cashier_html)
        self.assertIn('data-open-modal="edit-order-modal-17">Edit</button>', cashier_html)
        self.assertIn('data-open-modal="add-products-modal-17">Add</button>', cashier_html)
        self.assertIn('href="/orders?action=details&amp;order=17">Pay</a>', cashier_html)
        self.assertIn('id="new-order-modal-8"', cashier_html)
        self.assertIn('id="add-products-modal-17"', cashier_html)
        self.assertIn('data-open-modal="new-order-modal-8"', admin_html)
        self.assertIn('data-open-modal="add-products-modal-17"', admin_html)
        self.assertIn('id="add-products-modal-17"', admin_html)
        self.assertIn('data-open-modal="edit-order-modal-17">Edit</button>', admin_html)
        self.assertIn('data-open-modal="add-products-modal-17">Add</button>', admin_html)
        self.assertIn('href="/orders?action=details&amp;order=17">Pay</a>', admin_html)
        self.assertIn('Order #17: Cerveza', admin_html)
        self.assertIn('min-height:160px', app.UI_CSS)

    def test_any_role_can_add_products_to_an_open_order_created_by_another_user(self):
        app.CURRENT_USER_NAME = 'New User'

        for role in ('Mesero', 'Cajero', 'Administrador'):
            with self.subTest(role=role):
                html = app.orders_screen(role)
                self.assertIn('data-open-modal="add-products-modal-17"', html)
                self.assertNotIn('Products can only be added by the waiter', html)

    def test_table_management_only_lists_table_state_and_does_not_toggle_it(self):
        html = app.tables_screen('Administrador')

        self.assertIn('<th>Table</th><th>Location</th><th>Status</th><th>Seats</th>', html)
        self.assertIn('Table 08', html)
        self.assertIn('Table 09', html)
        self.assertNotIn('Enable', html)
        self.assertNotIn('Disable', html)
        self.assertNotIn('action="/actions/table-status"', html)

    def test_waiter_can_open_add_products_modal_for_an_open_order(self):
        html = app.orders_screen('Mesero')

        self.assertIn('data-open-modal="add-products-modal-17"', html)
        self.assertIn('Add products', html)
        self.assertIn('id="add-products-modal-17"', html)
        self.assertIn('action="/actions/order-items"', html)
        self.assertIn('name="order_id" value="17"', html)
        self.assertIn('name="product_id"', html)

    def test_add_products_modal_shows_existing_items_and_quantity_for_reordering(self):
        order = {
            'id': 17,
            'items': [
                {'product_id': 1, 'name': 'Cerveza Artesanal', 'quantity': 2, 'price': 12000},
                {'product_id': 1, 'name': 'Cerveza Artesanal', 'quantity': 1, 'price': 12000},
            ],
        }

        modal = app.english_markup(app.order_entry_modal('add', order))

        self.assertIn('Products already in this order', modal)
        self.assertIn(
            '<li><span>Cerveza Artesanal<strong class="existing-quantity">3</strong></span>',
            modal,
        )
        self.assertIn('class="outline add-existing-product" data-product-id="1"', modal)
        self.assertIn('Already in order: 3', modal)
        self.assertIn('name="product_id"', modal)
        self.assertIn('name="quantity"', modal)
        self.assertIn('data-stock="4"', modal)
        self.assertIn("event.target.closest('.add-existing-product')", app.orders_screen('Mesero'))

    def test_modal_lists_active_out_of_stock_products_as_unavailable(self):
        app.PRODUCTS = [
            {'id': 1, 'name': 'In stock', 'price': 100, 'stock': 2, 'active': True},
            {'id': 2, 'name': 'Out of stock', 'price': 200, 'stock': 0, 'active': True},
            {'id': 3, 'name': 'Inactive', 'price': 300, 'stock': 4, 'active': False},
        ]

        modal = app.order_entry_modal('add', {'id': 17, 'items': []})

        self.assertIn('In stock', modal)
        self.assertIn('Out of stock', modal)
        self.assertIn('data-stock="0" disabled', modal)
        self.assertNotIn('Inactive', modal)

    def test_refresh_frontend_data_caches_the_updated_bootstrap(self):
        user = {'username': 'waiter', 'backend_cookie': 'session', 'active_location_id': 8}
        bootstrap = {
            'tables': [], 'locations': [], 'products': [], 'orders': [],
            'active_location_id': 8,
        }
        app.BOOTSTRAP_CACHE.clear()

        with patch.object(app, 'request', return_value=(200, bootstrap, '')) as request:
            self.assertEqual(app.refresh_frontend_data(user), 200)

        request.assert_called_once_with('/api/bootstrap', cookie='session', location_id=8)
        self.assertEqual(app.BOOTSTRAP_CACHE['waiter:8'][1], bootstrap)

    def test_order_modal_can_search_products_and_limits_quantity_to_available_stock(self):
        modal = app.order_entry_modal('create', selected_table_id='8')
        html = app.orders_screen('Mesero')

        self.assertIn('class="product-search"', modal)
        self.assertIn('placeholder="Search products…"', modal)
        self.assertIn('data-stock="4"', modal)
        self.assertIn('name="quantity" min="1" value="1"', modal)
        self.assertIn('name="table_id" value="8"', modal)
        self.assertNotIn('<select name="table_id"', modal)
        self.assertIn('option.hidden = Boolean(query', html)
        self.assertIn('quantity.max = stock', html)

    def test_selecting_a_table_url_opens_the_order_modal_for_that_table(self):
        html = app.orders_screen('Mesero', selected_table_id='8')

        self.assertIn('id="new-order-modal-8"', html)
        self.assertIn('name="table_id" value="8"', html)
        self.assertIn('document.getElementById("new-order-modal-8").showModal()', html)

    def test_open_table_url_opens_add_products_modal_for_existing_order(self):
        app.CURRENT_USER_NAME = 'New User'

        html = app.orders_screen('Mesero', selected_order_id='17')

        self.assertIn('id="add-products-modal-17"', html)
        self.assertIn('document.getElementById("add-products-modal-17").showModal()', html)

    def test_invoice_uses_persisted_number_and_payment_method(self):
        app.ORDERS_FRONT[0].update({
            'status': 'Cerrado',
            'invoice_number': 'FV-0000017',
            'method': 'Debito',
        })

        html = app.cashier_orders_screen('Cajero', 'invoice', '17')

        self.assertIn('FV-0000017', html)
        self.assertIn('Debit', html)
        self.assertIn('Print invoice', html)

    def test_invoice_is_not_fabricated_when_order_has_no_persisted_invoice(self):
        html = app.cashier_orders_screen('Cajero', 'invoice', '17')

        self.assertIn('The invoice for this order has not been generated', html)
        self.assertNotIn('FV-0000017', html)

    def test_payment_requires_a_loaded_order_instead_of_fabricating_data(self):
        app.ORDERS_FRONT = []

        html = app.payment_screen('Cajero', '999')

        self.assertIn('The selected order was not found', html)
        self.assertNotIn('Record payment</h1>', html)

    def test_table_management_uses_database_location_ids(self):
        html = app.tables_screen('Administrador')

        self.assertIn('value="3"', html)
        self.assertIn('value="8"', html)
        self.assertIn('<td>Sede Sur</td>', html)

    def test_location_and_supplier_forms_support_editing(self):
        location_html = app.locations_screen('Administrador', '8')
        supplier_html = app.suppliers_screen('Administrador', edit_id='5')

        self.assertIn('location-update', location_html)
        self.assertIn('Carrera 4', location_html)
        self.assertIn('supplier-update', supplier_html)
        self.assertIn('Proveedor A', supplier_html)

    def test_admin_can_edit_user_profile_and_location(self):
        html = app.users_screen('Administrador', edit_id='4')

        self.assertIn('/actions/user-update', html)
        self.assertIn('name="role"', html)
        self.assertIn('value="Mesero" selected', html)
        self.assertIn('value="3" selected', html)
        self.assertIn('Laura Gómez', html)

    def test_user_form_hides_inactive_locations(self):
        app.LOCATION_ACTIVE = {3: False, 8: True}

        html = app.users_screen('Administrador')

        self.assertNotIn('<option value="3">Sede Norte</option>', html)
        self.assertIn('<option value="8">Sede Sur</option>', html)

    def test_waiter_can_review_orders_but_not_access_inventory(self):
        html = app.orders_screen('Mesero')

        self.assertIn('data-open-modal="new-order-modal-8"', html)
        self.assertIn('Create order', html)
        self.assertNotIn('Pagar</a>', html)
        self.assertNotIn('inventory', ROLE_ALLOWED['Mesero'])

    def test_screens_render_in_english_and_keep_backend_values_unchanged(self):
        html = app.users_screen('Administrador', edit_id='4')

        self.assertIn('<html lang="en">', html)
        self.assertIn('User management', html)
        self.assertIn('<option value="Mesero" selected>Waiter</option>', html)
        self.assertIn('href="/logout"', html)
        location_html = app.users_screen('Administrador')
        self.assertIn('<option value="8">Sede Sur</option>', location_html)
        notice_html = app.append_notice(app.users_screen('Administrador'), app.safe('Usuario registrado correctamente'))
        self.assertIn('User created successfully.', notice_html)
        inventory_html = app.inventory_screen('Administrador', 'entry')
        self.assertIn('value="Active location" readonly', inventory_html)
        self.assertIn('name="type" value="Entrada"', inventory_html)


if __name__ == '__main__':
    unittest.main()
