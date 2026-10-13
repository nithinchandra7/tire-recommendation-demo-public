-- Read-only diagnostics, not an automatic publishing gate. Require zero violations before release.
SELECT 'duplicate_product_id' AS check_name, COUNT(*) AS violations
FROM (SELECT product_id FROM product GROUP BY product_id HAVING COUNT(*)>1)
UNION ALL
SELECT 'duplicate_inventory_key',COUNT(*)
FROM (SELECT product_id,store_id FROM inventory GROUP BY product_id,store_id HAVING COUNT(*)>1)
UNION ALL
SELECT 'invalid_product_values',COUNT(*) FROM product
WHERE product_id IS NULL OR size IS NULL OR price IS NULL OR price<=0
  OR comfort IS NULL OR comfort NOT BETWEEN 1 AND 10
  OR wet_grip IS NULL OR wet_grip NOT BETWEEN 1 AND 10
  OR load_index IS NULL OR load_index NOT BETWEEN 75 AND 130
  OR speed_rank IS NULL OR speed_rank NOT BETWEEN 1 AND 6
UNION ALL
SELECT 'orphan_inventory',COUNT(*) FROM inventory i
LEFT JOIN product p ON p.product_id=i.product_id LEFT JOIN location l ON l.store_id=i.store_id
WHERE p.product_id IS NULL OR l.store_id IS NULL
UNION ALL
SELECT 'invalid_stock',COUNT(*) FROM inventory
WHERE quantity IS NULL OR quantity<0 OR observed_epoch IS NULL
  OR observed_epoch>DATE_PART(EPOCH_SECOND,CURRENT_TIMESTAMP())
UNION ALL
SELECT 'orphan_scope',COUNT(*) FROM retailer_scope r LEFT JOIN location l ON r.store_id=l.store_id
WHERE r.retailer_id IS NULL OR l.store_id IS NULL
UNION ALL
SELECT 'invalid_location',COUNT(*) FROM location
WHERE store_id IS NULL OR latitude IS NULL OR longitude IS NULL OR lead_days IS NULL OR lead_days<0
UNION ALL
SELECT 'invalid_fitment',COUNT(*) FROM vehicle
WHERE vehicle_id IS NULL OR size IS NULL OR min_load_index IS NULL OR min_speed_rank IS NULL
  OR fitment_version IS NULL;
