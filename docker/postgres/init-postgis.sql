-- =====================================================================
-- PostGIS + TimescaleDB Initialization Script
-- =====================================================================
-- This runs automatically on FIRST container boot via the
-- docker-entrypoint-initdb.d mechanism.
--
-- PostGIS extensions installed:
--   postgis          : Core spatial types (geometry, geography) + functions
--   postgis_topology : Topological spatial relationships
--   postgis_raster   : Raster/grid data storage and analysis (DEM, satellite)
-- =====================================================================

-- Core spatial engine
CREATE EXTENSION IF NOT EXISTS postgis CASCADE;

-- Topology for connected spatial networks (rivers, roads)
CREATE EXTENSION IF NOT EXISTS postgis_topology CASCADE;

-- Raster support for DEM tiles, satellite grids
CREATE EXTENSION IF NOT EXISTS postgis_raster CASCADE;

-- TimescaleDB for time-series hypertables
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Verify installations
DO $$
BEGIN
    RAISE NOTICE 'PostGIS version: %', PostGIS_Version();
    RAISE NOTICE 'All spatial extensions installed successfully.';
END $$;
