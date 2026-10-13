WITH scoped AS (
  SELECT p.*, i.store_id, l.name AS location_name, l.kind, l.lead_days,
    distance_miles(l.latitude,l.longitude,%(latitude)s,%(longitude)s) AS distance,
    CASE WHEN i.store_id=%(store_id)s AND %(scenario)s='nearby' THEN 0
         WHEN i.store_id=%(store_id)s AND %(scenario)s='quantity' THEN 2
         ELSE i.quantity END AS available_quantity,
    CASE WHEN i.store_id=%(store_id)s AND %(scenario)s='stale' THEN %(as_of)s-7200
         ELSE i.observed_epoch END AS observed_epoch
  FROM product p JOIN inventory i ON p.product_id=i.product_id
  JOIN location l ON l.store_id=i.store_id
  JOIN retailer_scope rs ON rs.store_id=i.store_id AND rs.retailer_id=%(retailer_id)s
), eligible AS (
  SELECT * FROM scoped WHERE size=%(size)s AND load_index>=%(min_load)s AND speed_rank>=%(min_speed)s
    AND (%(season)s='any' OR season=%(season)s) AND price<=%(budget)s
    AND available_quantity>=%(quantity)s AND observed_epoch>=%(fresh_after)s
    AND observed_epoch<=%(as_of)s AND lead_days<=%(max_lead)s
), features AS (
  SELECT *, comfort/10.0 AS comfort_feature, wet_grip/10.0 AS wet_feature,
    CASE WHEN distance>75 THEN 0 ELSE 1-distance/75.0 END AS proximity_feature,
    CASE WHEN %(budget)s<=0 THEN 0 ELSE 1-price/%(budget)s END AS price_feature,
    CASE WHEN lead_days=0 THEN 1 ELSE 1-lead_days/15.0 END AS delivery_feature
  FROM eligible
), scored AS (
  SELECT *, ROUND(100*(%(w_comfort)s*comfort_feature + %(w_wet)s*wet_feature
    + %(w_price)s*price_feature + %(w_distance)s*proximity_feature + %(w_delivery)s*delivery_feature),3) AS score
  FROM features
)
SELECT * FROM scored ORDER BY score DESC, price ASC, product_id ASC, store_id ASC;
