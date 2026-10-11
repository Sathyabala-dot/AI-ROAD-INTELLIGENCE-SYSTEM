-- ============================================================
-- Module 2 - Road Health Prediction System
-- PostgreSQL + PostGIS Database Schema
-- ============================================================
--
-- Database architecture:
--
--     roads
--       |
--       v
--     road_observations
--       |
--       v
--     road_health_predictions
--
-- One road can have many observations.
-- One observation can have one or more predictions.
--
-- This schema is designed to work with:
--     api/routes.py
--     database/connection.py
-- ============================================================


-- ============================================================
-- 1. ENABLE POSTGIS
-- ============================================================

CREATE EXTENSION IF NOT EXISTS postgis;


-- ============================================================
-- 2. ROADS TABLE
-- ============================================================
--
-- Stores relatively stable information about each road.
--
-- Dynamic observation data must NOT be stored here.
-- Dynamic data belongs in road_observations.
-- ============================================================

CREATE TABLE IF NOT EXISTS roads (
    road_id VARCHAR(20) PRIMARY KEY,

    road_name VARCHAR(255),

    road_type VARCHAR(100),

    road_length_km DOUBLE PRECISION
        CHECK (
            road_length_km IS NULL
            OR road_length_km >= 0
        ),

    road_age_years INTEGER
        CHECK (
            road_age_years IS NULL
            OR road_age_years >= 0
        ),

    lane_count INTEGER
        CHECK (
            lane_count IS NULL
            OR lane_count >= 1
        ),

    -- Road geometry.
    -- SRID 4326 = WGS84 latitude/longitude.
    geometry GEOMETRY(LineString, 4326),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 3. ROAD OBSERVATIONS TABLE
-- ============================================================
--
-- Stores the actual observation/input used for prediction.
--
-- IMPORTANT:
-- Every /predict/road request creates one observation row.
--
-- The generated observation_id is then stored in
-- road_health_predictions.observation_id.
-- ============================================================

CREATE TABLE IF NOT EXISTS road_observations (
    observation_id BIGSERIAL PRIMARY KEY,

    road_id VARCHAR(20) NOT NULL,

    "timestamp" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- --------------------------------------------------------
    -- Road damage
    -- --------------------------------------------------------

    pothole_count INTEGER NOT NULL
        CHECK (pothole_count >= 0),

    damage_count INTEGER NOT NULL
        CHECK (damage_count >= 0),

    damage_type VARCHAR(100),

    damage_severity INTEGER NOT NULL DEFAULT 0
        CHECK (
            damage_severity >= 0
            AND damage_severity <= 5
        ),

    damaged_area_percent DOUBLE PRECISION NOT NULL
        CHECK (
            damaged_area_percent >= 0
            AND damaged_area_percent <= 100
        ),

    -- --------------------------------------------------------
    -- Traffic
    -- --------------------------------------------------------

    vehicle_count INTEGER NOT NULL
        CHECK (vehicle_count >= 0),

    -- --------------------------------------------------------
    -- ML detection confidence
    -- --------------------------------------------------------

    confidence_score DOUBLE PRECISION NOT NULL
        CHECK (
            confidence_score >= 0
            AND confidence_score <= 1
        ),

    -- --------------------------------------------------------
    -- Weather
    -- --------------------------------------------------------

    rainfall_mm DOUBLE PRECISION DEFAULT 0
        CHECK (
            rainfall_mm IS NULL
            OR rainfall_mm >= 0
        ),

    temperature_c DOUBLE PRECISION,

    humidity_pct DOUBLE PRECISION
        CHECK (
            humidity_pct IS NULL
            OR (
                humidity_pct >= 0
                AND humidity_pct <= 100
            )
        ),

    weather_condition VARCHAR(100),

    -- --------------------------------------------------------
    -- Maintenance
    -- --------------------------------------------------------

    days_since_maintenance INTEGER
        CHECK (
            days_since_maintenance IS NULL
            OR days_since_maintenance >= 0
        ),

    maintenance_count_last_year INTEGER
        CHECK (
            maintenance_count_last_year IS NULL
            OR maintenance_count_last_year >= 0
        ),

    -- --------------------------------------------------------
    -- Accident history
    -- --------------------------------------------------------

    historical_accident_count INTEGER DEFAULT 0
        CHECK (
            historical_accident_count IS NULL
            OR historical_accident_count >= 0
        ),

    -- --------------------------------------------------------
    -- Observation location
    -- --------------------------------------------------------

    latitude DOUBLE PRECISION
        CHECK (
            latitude IS NULL
            OR (
                latitude >= -90
                AND latitude <= 90
            )
        ),

    longitude DOUBLE PRECISION
        CHECK (
            longitude IS NULL
            OR (
                longitude >= -180
                AND longitude <= 180
            )
        ),

    -- PostGIS point generated from latitude/longitude.
    geom GEOMETRY(Point, 4326),

    -- --------------------------------------------------------
    -- Record creation time
    -- --------------------------------------------------------

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- --------------------------------------------------------
    -- Foreign key
    -- --------------------------------------------------------

    CONSTRAINT fk_observation_road
        FOREIGN KEY (road_id)
        REFERENCES roads (road_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


-- ============================================================
-- 4. ROAD HEALTH PREDICTIONS TABLE
-- ============================================================
--
-- Stores the output generated from a road observation.
--
-- IMPORTANT RELATIONSHIP:
--
--     road_health_predictions.observation_id
--                    |
--                    v
--          road_observations.observation_id
--
-- This allows every prediction to be traced back to the
-- exact input observation that produced it.
-- ============================================================

CREATE TABLE IF NOT EXISTS road_health_predictions (
    prediction_id BIGSERIAL PRIMARY KEY,

    road_id VARCHAR(20) NOT NULL,

    observation_id BIGINT NOT NULL,

    prediction_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- --------------------------------------------------------
    -- Road Health Score
    -- --------------------------------------------------------

    health_score DOUBLE PRECISION NOT NULL
        CHECK (
            health_score >= 0
            AND health_score <= 100
        ),

    condition VARCHAR(50) NOT NULL,

    -- --------------------------------------------------------
    -- Additional Module 2 predictions
    -- --------------------------------------------------------

    congestion_level VARCHAR(50) NOT NULL,

    accident_risk VARCHAR(50) NOT NULL,

    maintenance_priority VARCHAR(50) NOT NULL,

    -- --------------------------------------------------------
    -- Prediction location
    -- --------------------------------------------------------

    latitude DOUBLE PRECISION
        CHECK (
            latitude IS NULL
            OR (
                latitude >= -90
                AND latitude <= 90
            )
        ),

    longitude DOUBLE PRECISION
        CHECK (
            longitude IS NULL
            OR (
                longitude >= -180
                AND longitude <= 180
            )
        ),

    -- PostGIS point generated from latitude/longitude.
    geom GEOMETRY(Point, 4326),

    -- --------------------------------------------------------
    -- Model version
    -- --------------------------------------------------------
    --
    -- This is important for tracking which model produced
    -- a prediction.
    --

    model_version VARCHAR(100) NOT NULL
        DEFAULT 'road_health_model_v1',

    -- --------------------------------------------------------
    -- Foreign keys
    -- --------------------------------------------------------

    CONSTRAINT fk_prediction_road
        FOREIGN KEY (road_id)
        REFERENCES roads (road_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    CONSTRAINT fk_prediction_observation
        FOREIGN KEY (observation_id)
        REFERENCES road_observations (observation_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


-- ============================================================
-- 5. INDEXES
-- ============================================================

-- ------------------------------------------------------------
-- Roads
-- ------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_roads_road_type
    ON roads (road_type);

CREATE INDEX IF NOT EXISTS idx_roads_geometry
    ON roads
    USING GIST (geometry);


-- ------------------------------------------------------------
-- Road observations
-- ------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_observations_road_id
    ON road_observations (road_id);

CREATE INDEX IF NOT EXISTS idx_observations_timestamp
    ON road_observations ("timestamp");

CREATE INDEX IF NOT EXISTS idx_observations_road_timestamp
    ON road_observations (road_id, "timestamp" DESC);

CREATE INDEX IF NOT EXISTS idx_observations_geom
    ON road_observations
    USING GIST (geom);


-- ------------------------------------------------------------
-- Predictions
-- ------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_predictions_road_id
    ON road_health_predictions (road_id);

CREATE INDEX IF NOT EXISTS idx_predictions_observation_id
    ON road_health_predictions (observation_id);

CREATE INDEX IF NOT EXISTS idx_predictions_prediction_time
    ON road_health_predictions (prediction_time);

CREATE INDEX IF NOT EXISTS idx_predictions_road_time
    ON road_health_predictions (
        road_id,
        prediction_time DESC
    );

CREATE INDEX IF NOT EXISTS idx_predictions_geom
    ON road_health_predictions
    USING GIST (geom);


-- ============================================================
-- 6. FUNCTION - UPDATE ROAD GEOMETRY
-- ============================================================
--
-- If a road's geometry is supplied separately, it can be
-- stored directly in roads.geometry.
--
-- No automatic geometry is generated here because a road
-- geometry requires a LineString, not a single point.
-- ============================================================


-- ============================================================
-- 7. FUNCTION - CREATE OBSERVATION POINT GEOMETRY
-- ============================================================
--
-- Automatically creates:
--
--     POINT(longitude latitude)
--
-- when latitude and longitude are available.
-- ============================================================

CREATE OR REPLACE FUNCTION set_observation_geom()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN

    IF NEW.latitude IS NOT NULL
       AND NEW.longitude IS NOT NULL THEN

        NEW.geom :=
            ST_SetSRID(
                ST_MakePoint(
                    NEW.longitude,
                    NEW.latitude
                ),
                4326
            );

    ELSE

        NEW.geom := NULL;

    END IF;

    RETURN NEW;

END;
$$;


-- ============================================================
-- 8. OBSERVATION GEOMETRY TRIGGER
-- ============================================================

DROP TRIGGER IF EXISTS trg_set_observation_geom
ON road_observations;

CREATE TRIGGER trg_set_observation_geom
BEFORE INSERT OR UPDATE OF latitude, longitude
ON road_observations
FOR EACH ROW
EXECUTE FUNCTION set_observation_geom();


-- ============================================================
-- 9. FUNCTION - CREATE PREDICTION POINT GEOMETRY
-- ============================================================
--
-- Automatically creates prediction location geometry from
-- latitude and longitude.
-- ============================================================

CREATE OR REPLACE FUNCTION set_prediction_geom()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN

    IF NEW.latitude IS NOT NULL
       AND NEW.longitude IS NOT NULL THEN

        NEW.geom :=
            ST_SetSRID(
                ST_MakePoint(
                    NEW.longitude,
                    NEW.latitude
                ),
                4326
            );

    ELSE

        NEW.geom := NULL;

    END IF;

    RETURN NEW;

END;
$$;


-- ============================================================
-- 10. PREDICTION GEOMETRY TRIGGER
-- ============================================================

DROP TRIGGER IF EXISTS trg_set_prediction_geom
ON road_health_predictions;

CREATE TRIGGER trg_set_prediction_geom
BEFORE INSERT OR UPDATE OF latitude, longitude
ON road_health_predictions
FOR EACH ROW
EXECUTE FUNCTION set_prediction_geom();


-- ============================================================
-- 11. FUNCTION - UPDATE roads.updated_at
-- ============================================================

CREATE OR REPLACE FUNCTION update_road_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN

    NEW.updated_at := CURRENT_TIMESTAMP;

    RETURN NEW;

END;
$$;


-- ============================================================
-- 12. ROADS UPDATED_AT TRIGGER
-- ============================================================

DROP TRIGGER IF EXISTS trg_update_road_updated_at
ON roads;

CREATE TRIGGER trg_update_road_updated_at
BEFORE UPDATE
ON roads
FOR EACH ROW
EXECUTE FUNCTION update_road_updated_at();


-- ============================================================
-- 13. OPTIONAL COMMENTS
-- ============================================================

COMMENT ON TABLE roads IS
    'Master information for each road segment.';

COMMENT ON TABLE road_observations IS
    'Individual road condition, traffic, weather and maintenance observations.';

COMMENT ON TABLE road_health_predictions IS
    'Predictions generated from individual road observations.';

COMMENT ON COLUMN road_health_predictions.observation_id IS
    'Links the prediction to the exact road observation that produced it.';

COMMENT ON COLUMN road_health_predictions.model_version IS
    'Version/name of the ML model used to generate the prediction.';

COMMENT ON COLUMN road_observations.geom IS
    'PostGIS point generated from observation longitude and latitude.';

COMMENT ON COLUMN road_health_predictions.geom IS
    'PostGIS point generated from prediction longitude and latitude.';


-- ============================================================
-- 14. VERIFICATION
-- ============================================================
--
-- These queries are intentionally read-only.
-- They help verify that the expected tables exist.
-- ============================================================

SELECT
    table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
      'roads',
      'road_observations',
      'road_health_predictions'
  )
ORDER BY table_name;

--One important correction
--Your existing database/__init__.py had the dangerous legacy behavior of connecting to PostgreSQL and dropping/creating old tables on import. This new schema.sql does not contain that legacy architecture.
--Also, this schema is deliberately not creating the old tables:
--
--road_segments
--road_images
--road_conditions
--road_health_scores
--model_details
--predictions
--Those belong to the old/conflicting database design and should not be brought back.