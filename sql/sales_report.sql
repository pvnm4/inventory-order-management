-- Units sold and revenue per product for orders created in [:start_ts, :end_ts).
SELECT
    p.id                              AS product_id,
    p.sku                             AS sku,
    p.name                            AS name,
    SUM(oi.quantity)                  AS units_sold,
    SUM(oi.quantity * oi.unit_price)  AS revenue
FROM order_items AS oi
JOIN orders   AS o ON o.id = oi.order_id
JOIN products AS p ON p.id = oi.product_id
WHERE o.status = 'confirmed'
  AND o.created_at >= :start_ts
  AND o.created_at <  :end_ts
GROUP BY p.id, p.sku, p.name
ORDER BY revenue DESC, p.id ASC;
