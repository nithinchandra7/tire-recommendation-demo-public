PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS product (
  product_id TEXT PRIMARY KEY, brand TEXT NOT NULL, name TEXT NOT NULL,
  size TEXT NOT NULL, load_index INTEGER NOT NULL CHECK(load_index BETWEEN 75 AND 130),
  speed_rank INTEGER NOT NULL CHECK(speed_rank BETWEEN 1 AND 6), speed_symbol TEXT NOT NULL,
  season TEXT NOT NULL, price REAL NOT NULL CHECK(price > 0),
  comfort INTEGER NOT NULL CHECK(comfort BETWEEN 1 AND 10),
  wet_grip INTEGER NOT NULL CHECK(wet_grip BETWEEN 1 AND 10),
  warranty_miles INTEGER NOT NULL, tier TEXT NOT NULL, description TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS location (
  store_id TEXT PRIMARY KEY, name TEXT NOT NULL, kind TEXT NOT NULL,
  latitude REAL NOT NULL, longitude REAL NOT NULL, lead_days INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS vehicle (
  vehicle_id TEXT PRIMARY KEY, name TEXT NOT NULL, size TEXT NOT NULL,
  min_load_index INTEGER NOT NULL, min_speed_rank INTEGER NOT NULL, fitment_version TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS inventory (
  product_id TEXT REFERENCES product(product_id), store_id TEXT REFERENCES location(store_id),
  quantity INTEGER NOT NULL CHECK(quantity >= 0), observed_epoch INTEGER NOT NULL,
  PRIMARY KEY(product_id,store_id)
);
CREATE TABLE IF NOT EXISTS retailer_scope (
  retailer_id TEXT NOT NULL, store_id TEXT REFERENCES location(store_id),
  PRIMARY KEY(retailer_id,store_id)
);
CREATE TABLE IF NOT EXISTS session_state (
  session_id TEXT PRIMARY KEY, retailer_id TEXT NOT NULL, revision INTEGER NOT NULL,
  filters_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS inventory_event (
  event_id TEXT PRIMARY KEY, payload_json TEXT NOT NULL, outcome TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS product_eligibility ON product(size,load_index,speed_rank);
