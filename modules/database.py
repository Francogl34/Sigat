import os
import psycopg2
import psycopg2.extras
from psycopg2 import pool
from datetime import datetime


DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME", "sigat_db"),
    "user": os.getenv("DB_USER", "sigat_user"),
    "password": os.getenv("DB_PASSWORD", "sigat_pass"),
}

_pool = None


def get_pool():
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            **DB_CONFIG
        )
    return _pool


def get_connection():
    return get_pool().getconn()


def release_connection(conn):
    get_pool().putconn(conn)


def execute_query(sql, params=None, fetch=False):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            if fetch:
                result = cur.fetchall()
                conn.commit()
                return [dict(row) for row in result]
            conn.commit()
            return cur.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        release_connection(conn)


def execute_one(sql, params=None):
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            conn.commit()
            return dict(row) if row else None
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        release_connection(conn)


def init_db():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sensors (
                    id VARCHAR(20) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    lat DOUBLE PRECISION NOT NULL,
                    lng DOUBLE PRECISION NOT NULL,
                    zone_id VARCHAR(20),
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    id SERIAL PRIMARY KEY,
                    sensor_id VARCHAR(20) REFERENCES sensors(id),
                    temperature DOUBLE PRECISION,
                    humidity DOUBLE PRECISION,
                    smoke_ppm DOUBLE PRECISION,
                    wind_speed DOUBLE PRECISION,
                    co2_ppm DOUBLE PRECISION,
                    risk_level VARCHAR(20),
                    recorded_at TIMESTAMP DEFAULT NOW()
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS zones (
                    id VARCHAR(20) PRIMARY KEY,
                    name VARCHAR(150) NOT NULL,
                    area_ha DOUBLE PRECISION,
                    vegetation VARCHAR(100),
                    altitude_m INTEGER,
                    priority VARCHAR(20),
                    last_incident DATE,
                    population_nearby INTEGER,
                    lat DOUBLE PRECISION,
                    lng DOUBLE PRECISION
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    sensor_id VARCHAR(20) REFERENCES sensors(id),
                    zone VARCHAR(150),
                    level VARCHAR(20),
                    message TEXT,
                    temperature DOUBLE PRECISION,
                    humidity DOUBLE PRECISION,
                    smoke_ppm DOUBLE PRECISION,
                    wind_speed DOUBLE PRECISION,
                    recommended_action TEXT,
                    color VARCHAR(10),
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id SERIAL PRIMARY KEY,
                    sensor_id VARCHAR(20) REFERENCES sensors(id),
                    zone VARCHAR(150),
                    current_probability DOUBLE PRECISION,
                    trend VARCHAR(30),
                    forecast_3h DOUBLE PRECISION,
                    forecast_6h DOUBLE PRECISION,
                    forecast_12h DOUBLE PRECISION,
                    confidence DOUBLE PRECISION,
                    risk_factors TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS hourly_history (
                    id SERIAL PRIMARY KEY,
                    hour VARCHAR(10),
                    avg_temp DOUBLE PRECISION,
                    avg_humidity DOUBLE PRECISION,
                    avg_smoke DOUBLE PRECISION,
                    incidents INTEGER DEFAULT 0,
                    recorded_at TIMESTAMP DEFAULT NOW()
                );
            """)

            cur.execute("""
                INSERT INTO sensors (id, name, lat, lng) VALUES
                    ('SEN-001', 'Sector Tunari Norte', -17.340, -66.215),
                    ('SEN-002', 'Sector Tunari Centro', -17.355, -66.240),
                    ('SEN-003', 'Sector Tunari Sur', -17.370, -66.225),
                    ('SEN-004', 'Quebrada Saytu Kocha', -17.345, -66.260),
                    ('SEN-005', 'Bosque Sacaba', -17.385, -66.050),
                    ('SEN-006', 'Parque Alalay', -17.395, -66.140)
                ON CONFLICT (id) DO NOTHING;
            """)

            cur.execute("""
                INSERT INTO zones (id, name, area_ha, vegetation, altitude_m, priority, last_incident, population_nearby, lat, lng) VALUES
                    ('Z001', 'Parque Nacional Tunari Norte', 4850, 'Bosque montano', 2800, 'Alta', '2024-08-15', 12500, -17.340, -66.215),
                    ('Z002', 'Parque Nacional Tunari Centro', 6200, 'Queñuales y matorrales', 3200, 'Crítica', '2025-09-03', 8200, -17.355, -66.240),
                    ('Z003', 'Parque Nacional Tunari Sur', 3900, 'Pino y eucalipto', 2600, 'Media', '2024-07-22', 22000, -17.370, -66.225),
                    ('Z004', 'Quebrada Saytu Kocha', 1200, 'Vegetación riparia', 2500, 'Alta', '2025-10-11', 4500, -17.345, -66.260),
                    ('Z005', 'Bosque Sacaba', 890, 'Arbustos y pastizales', 2600, 'Media', '2023-09-05', 35000, -17.385, -66.050),
                    ('Z006', 'Área Verde Alalay', 320, 'Vegetación urbana', 2500, 'Baja', '2022-08-19', 85000, -17.395, -66.140)
                ON CONFLICT (id) DO NOTHING;
            """)

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        release_connection(conn)
