-- Review and run ONLY in a dedicated, configured sandbox schema.
-- Database/schema/warehouse are configured separately; no account details are embedded.
CREATE TABLE IF NOT EXISTS product (
  product_id VARCHAR PRIMARY KEY, brand VARCHAR, name VARCHAR, size VARCHAR,
  load_index INTEGER, speed_rank INTEGER, speed_symbol VARCHAR, season VARCHAR,
  price NUMBER(10,2), comfort INTEGER, wet_grip INTEGER, warranty_miles INTEGER,
  tier VARCHAR, description VARCHAR
);
CREATE TABLE IF NOT EXISTS location (
  store_id VARCHAR PRIMARY KEY, name VARCHAR, kind VARCHAR,
  latitude FLOAT, longitude FLOAT, lead_days INTEGER
);
CREATE TABLE IF NOT EXISTS vehicle (
  vehicle_id VARCHAR PRIMARY KEY, name VARCHAR, size VARCHAR,
  min_load_index INTEGER, min_speed_rank INTEGER, fitment_version VARCHAR
);
CREATE TABLE IF NOT EXISTS inventory (
  product_id VARCHAR, store_id VARCHAR, quantity INTEGER, observed_epoch INTEGER,
  PRIMARY KEY(product_id,store_id)
);
CREATE TABLE IF NOT EXISTS retailer_scope (
  retailer_id VARCHAR, store_id VARCHAR, PRIMARY KEY(retailer_id,store_id)
);
CREATE FUNCTION IF NOT EXISTS distance_miles(lat1 FLOAT,lon1 FLOAT,lat2 FLOAT,lon2 FLOAT)
RETURNS FLOAT LANGUAGE SQL AS $$
  3958.8 * 2 * ASIN(SQRT(LEAST(1.0,
    POW(SIN(RADIANS(lat2-lat1)/2),2) + COS(RADIANS(lat1))*COS(RADIANS(lat2))
    * POW(SIN(RADIANS(lon2-lon1)/2),2))))
$$;
-- Ordinary Snowflake key constraints are not enforcement substitutes.
-- Validate uniqueness, source IDs, value ranges, referential integrity and timestamp ordering
-- before publishing tables; review quality.sql. Epochs support consistent binding in both adapters.
