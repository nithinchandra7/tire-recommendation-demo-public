WITH scoped AS (
  SELECT p.*, i.store_id, l.name AS location_name, l.kind, l.lead_days,
    distance_miles(l.latitude,l.longitude,:latitude,:longitude) AS distance,
    CASE WHEN i.store_id=:store_id AND :scenario='nearby' THEN 0
         WHEN i.store_id=:store_id AND :scenario='quantity' THEN 2
         ELSE i.quantity END AS available_quantity,
    CASE WHEN i.store_id=:store_id AND :scenario='stale' THEN :as_of-7200
         ELSE i.observed_epoch END AS observed_epoch
  FROM product p JOIN inventory i ON p.product_id=i.product_id
  JOIN location l ON l.store_id=i.store_id
  JOIN retailer_scope rs ON rs.store_id=i.store_id AND rs.retailer_id=:retailer_id
), eligible AS (
  SELECT * FROM scoped WHERE size=:size AND load_index>=:min_load AND speed_rank>=:min_speed
    AND (:season='any' OR season=:season) AND price<=:budget
    AND available_quantity>=:quantity AND observed_epoch>=:fresh_after
    AND observed_epoch<=:as_of AND lead_days<=:max_lead
), features AS (
  SELECT *, comfort/10.0 AS comfort_feature, wet_grip/10.0 AS wet_feature,
    CASE WHEN distance>75 THEN 0 ELSE 1-distance/75.0 END AS proximity_feature,
    CASE WHEN :budget<=0 THEN 0 ELSE 1-price/:budget END AS price_feature,
    CASE WHEN lead_days=0 THEN 1 ELSE 1-lead_days/15.0 END AS delivery_feature
  FROM eligible
), scored AS (
  SELECT *, ROUND(100*(:w_comfort*comfort_feature + :w_wet*wet_feature
    + :w_price*price_feature + :w_distance*proximity_feature + :w_delivery*delivery_feature),3) AS score
  FROM features
)
SELECT * FROM scored ORDER BY score DESC, price ASC, product_id ASC, store_id ASC;
