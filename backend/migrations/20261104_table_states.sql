USE barwise;

UPDATE tables_bar t
LEFT JOIN (
    SELECT DISTINCT table_id
    FROM orders
    WHERE status IN ('Abierto', 'Pagado')
) open_orders ON open_orders.table_id = t.id
SET t.status = IF(open_orders.table_id IS NULL, 'Libre', 'Ocupada');

ALTER TABLE tables_bar
    MODIFY status ENUM('Libre', 'Ocupada') NOT NULL DEFAULT 'Libre';
