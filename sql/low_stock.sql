-- Products at or below a stock threshold.
-- :threshold  optional override; when NULL each product's own low_stock_threshold is used.
SELECT
    id                                          AS product_id,
    sku,
    name,
    stock_quantity,
    COALESCE(:threshold, low_stock_threshold)   AS threshold
FROM products
WHERE stock_quantity <= COALESCE(:threshold, low_stock_threshold)
ORDER BY stock_quantity ASC, id ASC;
