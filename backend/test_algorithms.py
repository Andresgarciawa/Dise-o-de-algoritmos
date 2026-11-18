import unittest

from algorithms import (binary_search_products, merge_sort_products,
                        inventory_alerts, calculate_order_total, sales_summary,
                        linear_search_products, quick_sort_orders,
                        consolidate_order_items, paginate, calculate_change,
                        inventory_projection, top_selling_products)


class AlgorithmTests(unittest.TestCase):
    def setUp(self):
        self.products = [
            {'id': 1, 'name': 'Whisky', 'code': 'WHI-001', 'stock': 4},
            {'id': 2, 'name': 'Cerveza', 'code': 'CER-001', 'stock': 20},
            {'id': 3, 'name': 'Gin', 'code': 'GIN-001', 'stock': 8},
        ]

    def test_binary_search_by_name_and_code(self):
        self.assertEqual(binary_search_products(self.products, 'Cerveza')['id'], 2)
        self.assertEqual(binary_search_products(self.products, 'GIN-001')['id'], 3)
        self.assertIsNone(binary_search_products(self.products, 'Vodka'))

    def test_merge_sort_descending_stock(self):
        result = merge_sort_products(self.products, 'stock', reverse=True)
        self.assertEqual([item['id'] for item in result], [2, 3, 1])

    def test_inventory_alerts(self):
        alerts = inventory_alerts([{'name': 'Whisky', 'quantity': 4, 'minimum_quantity': 5},
                                   {'name': 'Gin', 'quantity': 8, 'minimum_quantity': 5}])
        self.assertEqual([item['name'] for item in alerts], ['Whisky'])

    def test_order_total(self):
        result = calculate_order_total([{'name': 'Cerveza', 'quantity': 2, 'price': 12000}])
        self.assertEqual(result['items'][0]['subtotal'], 24000)
        self.assertEqual(result['total'], 24000)

    def test_sales_summary(self):
        result = sales_summary([{'date': '2026-11-01', 'total': 100},
                                {'date': '2026-11-01', 'total': 50}])
        self.assertEqual(result[0]['orders'], 2)
        self.assertEqual(result[0]['sales'], 150)
        self.assertEqual(result[0]['average_order'], 75)

    def test_linear_search(self):
        self.assertEqual(len(linear_search_products(self.products, 'gin')), 1)

    def test_quick_sort_orders(self):
        result = quick_sort_orders([{'id': 1, 'total': 20}, {'id': 2, 'total': 80}])
        self.assertEqual(result[0]['id'], 2)

    def test_consolidate_items(self):
        result = consolidate_order_items([{'product_id': 1, 'quantity': 2}, {'product_id': 1, 'quantity': 3}])
        self.assertEqual(result[0]['quantity'], 5)

    def test_paginate(self):
        result = paginate([1, 2, 3, 4, 5], 2, 2)
        self.assertEqual(result['items'], [3, 4])
        self.assertEqual(result['pages'], 3)

    def test_greedy_change(self):
        result = calculate_change(12500, 20000, [10000, 5000, 2000, 500, 100])
        self.assertEqual(result['total'], 7500)
        self.assertEqual(sum(result['denominations']), 7500)

    def test_inventory_projection(self):
        self.assertTrue(inventory_projection(5, 1, 7)['will_be_empty'])

    def test_top_selling_products(self):
        result = top_selling_products([{'product_id': 1, 'name': 'Beer', 'quantity': 2, 'price': 10},
                                       {'product_id': 1, 'name': 'Beer', 'quantity': 3, 'price': 10}])
        self.assertEqual(result[0]['quantity'], 5)


if __name__ == '__main__':
    unittest.main()
